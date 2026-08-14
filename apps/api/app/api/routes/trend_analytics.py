from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, ContentPillar, MetricSnapshot, Publication
from app.schemas_analytics import PillarTrendItem

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _latest_metric_snapshot_subquery():
    latest_times = (
        select(
            MetricSnapshot.publication_id,
            func.max(MetricSnapshot.captured_at).label("captured_at"),
        )
        .group_by(MetricSnapshot.publication_id)
        .subquery()
    )
    return (
        select(MetricSnapshot)
        .join(
            latest_times,
            (MetricSnapshot.publication_id == latest_times.c.publication_id)
            & (MetricSnapshot.captured_at == latest_times.c.captured_at),
        )
        .subquery()
    )


def _period_summary(items: list[tuple[int, int]]) -> tuple[int, float, float]:
    if not items:
        return 0, 0.0, 0.0
    total_views = sum(item[0] for item in items)
    total_favorites = sum(item[1] for item in items)
    return (
        len(items),
        round(total_views / len(items), 2),
        round(total_favorites / total_views * 100, 2) if total_views else 0.0,
    )


@router.get("/pillar-trends", response_model=list[PillarTrendItem])
def pillar_interest_trends(
    window_days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[PillarTrendItem]:
    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(days=window_days)
    previous_cutoff = now - timedelta(days=window_days * 2)
    latest = _latest_metric_snapshot_subquery()

    rows = db.execute(
        select(
            ContentPillar.id.label("pillar_id"),
            ContentPillar.name.label("pillar_name"),
            Publication.published_at,
            latest.c.views,
            latest.c.favorites,
        )
        .select_from(ContentPillar)
        .join(Content, Content.pillar_id == ContentPillar.id)
        .join(Publication, Publication.content_id == Content.id)
        .join(latest, latest.c.publication_id == Publication.id)
        .where(
            ContentPillar.user_id == user_id,
            Publication.published_at.is_not(None),
            Publication.published_at >= previous_cutoff,
        )
    ).all()

    grouped: dict[UUID, dict[str, object]] = defaultdict(
        lambda: {"name": "", "recent": [], "previous": []}
    )
    for row in rows:
        bucket = grouped[row.pillar_id]
        bucket["name"] = row.pillar_name
        pair = (int(row.views), int(row.favorites))
        if row.published_at >= recent_cutoff:
            bucket["recent"].append(pair)  # type: ignore[union-attr]
        else:
            bucket["previous"].append(pair)  # type: ignore[union-attr]

    result: list[PillarTrendItem] = []
    for pillar_id, bucket in grouped.items():
        recent_items = bucket["recent"]
        previous_items = bucket["previous"]
        recent_count, recent_avg_views, recent_favorite_rate = _period_summary(recent_items)  # type: ignore[arg-type]
        previous_count, previous_avg_views, previous_favorite_rate = _period_summary(previous_items)  # type: ignore[arg-type]

        change_percent: float | None = None
        if previous_avg_views > 0:
            change_percent = round(
                (recent_avg_views - previous_avg_views) / previous_avg_views * 100,
                2,
            )

        if recent_count == 0:
            signal = "insufficient"
        elif previous_count == 0:
            signal = "new"
        elif change_percent is not None and change_percent >= 20:
            signal = "rising"
        elif change_percent is not None and change_percent <= -20:
            signal = "falling"
        else:
            signal = "stable"

        result.append(
            PillarTrendItem(
                pillar_id=pillar_id,
                pillar_name=str(bucket["name"]),
                recent_publications=recent_count,
                previous_publications=previous_count,
                recent_avg_views=recent_avg_views,
                previous_avg_views=previous_avg_views,
                view_change_percent=change_percent,
                recent_favorite_rate=recent_favorite_rate,
                previous_favorite_rate=previous_favorite_rate,
                signal=signal,
            )
        )

    signal_order = {"rising": 0, "new": 1, "stable": 2, "falling": 3, "insufficient": 4}
    return sorted(
        result,
        key=lambda item: (signal_order[item.signal], -item.recent_avg_views),
    )
