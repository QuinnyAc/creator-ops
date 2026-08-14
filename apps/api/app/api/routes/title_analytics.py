from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, MetricSnapshot, Publication
from app.schemas_title_analytics import TitlePatternAnalyticsItem
from app.services.title_patterns import PATTERN_LABELS, classify_title_patterns

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/title-patterns", response_model=list[TitlePatternAnalyticsItem])
def analytics_by_title_pattern(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[TitlePatternAnalyticsItem]:
    latest_times = (
        select(
            MetricSnapshot.publication_id,
            func.max(MetricSnapshot.captured_at).label("captured_at"),
        )
        .group_by(MetricSnapshot.publication_id)
        .subquery()
    )
    latest = (
        select(MetricSnapshot)
        .join(
            latest_times,
            (MetricSnapshot.publication_id == latest_times.c.publication_id)
            & (MetricSnapshot.captured_at == latest_times.c.captured_at),
        )
        .subquery()
    )

    rows = db.execute(
        select(
            Publication.id,
            func.coalesce(Publication.title, Content.title).label("title"),
            latest.c.views,
            latest.c.likes,
            latest.c.comments,
            latest.c.favorites,
            latest.c.shares,
            latest.c.followers_gained,
        )
        .select_from(latest)
        .join(Publication, Publication.id == latest.c.publication_id)
        .join(Content, Content.id == Publication.content_id)
        .where(Content.user_id == user_id)
    ).all()

    totals: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "publications": 0,
            "views": 0,
            "likes": 0,
            "comments": 0,
            "favorites": 0,
            "shares": 0,
            "followers_gained": 0,
        }
    )

    for row in rows:
        for pattern in classify_title_patterns(row.title or ""):
            bucket = totals[pattern]
            bucket["publications"] += 1
            bucket["views"] += int(row.views)
            bucket["likes"] += int(row.likes)
            bucket["comments"] += int(row.comments)
            bucket["favorites"] += int(row.favorites)
            bucket["shares"] += int(row.shares)
            bucket["followers_gained"] += int(row.followers_gained)

    result: list[TitlePatternAnalyticsItem] = []
    for pattern, total in totals.items():
        publications = total["publications"]
        views = total["views"]
        interactions = total["likes"] + total["comments"] + total["favorites"] + total["shares"]
        result.append(
            TitlePatternAnalyticsItem(
                pattern=pattern,
                label=PATTERN_LABELS[pattern],
                publications=publications,
                views=views,
                likes=total["likes"],
                comments=total["comments"],
                favorites=total["favorites"],
                shares=total["shares"],
                followers_gained=total["followers_gained"],
                avg_views=round(views / publications, 2) if publications else 0.0,
                engagement_rate=round(interactions / views * 100, 2) if views else 0.0,
                favorite_rate=round(total["favorites"] / views * 100, 2) if views else 0.0,
                follower_conversion_rate=round(
                    total["followers_gained"] / views * 100,
                    2,
                )
                if views
                else 0.0,
            )
        )

    return sorted(
        result,
        key=lambda item: (item.avg_views, item.favorite_rate, item.engagement_rate),
        reverse=True,
    )
