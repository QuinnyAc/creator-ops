from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import (
    Content,
    ContentPillar,
    MetricSnapshot,
    Platform,
    PlatformAccount,
    Publication,
    Tag,
    content_tags,
)
from app.schemas import AnalyticsSummary, MetricSnapshotCreate, MetricSnapshotRead
from app.schemas_analytics import (
    PerformanceMilestone,
    PillarAnalyticsItem,
    PillarTrendItem,
    PlatformAnalyticsItem,
    TagAnalyticsItem,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])

MILESTONES = [
    ("24h", 24),
    ("72h", 72),
    ("7d", 24 * 7),
    ("30d", 24 * 30),
]


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


def _get_owned_publication(
    db: Session,
    publication_id: UUID,
    user_id: UUID,
) -> Publication:
    publication = db.scalar(
        select(Publication)
        .join(Content, Content.id == Publication.content_id)
        .where(Publication.id == publication_id, Content.user_id == user_id)
    )
    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found.")
    return publication


def _rates(
    publications: int,
    views: int,
    likes: int,
    comments: int,
    favorites: int,
    shares: int,
    followers: int,
) -> tuple[float, float, float, float]:
    interactions = likes + comments + favorites + shares
    return (
        round(views / publications, 2) if publications else 0.0,
        round(interactions / views * 100, 2) if views else 0.0,
        round(favorites / views * 100, 2) if views else 0.0,
        round(followers / views * 100, 2) if views else 0.0,
    )


@router.get("/publications/{publication_id}/metrics", response_model=list[MetricSnapshotRead])
def list_metrics(
    publication_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[MetricSnapshot]:
    _get_owned_publication(db, publication_id, user_id)
    return list(
        db.scalars(
            select(MetricSnapshot)
            .where(MetricSnapshot.publication_id == publication_id)
            .order_by(MetricSnapshot.captured_at.desc())
        )
    )


@router.post(
    "/publications/{publication_id}/metrics",
    response_model=MetricSnapshotRead,
    status_code=status.HTTP_201_CREATED,
)
def create_metric_snapshot(
    publication_id: UUID,
    payload: MetricSnapshotCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> MetricSnapshot:
    _get_owned_publication(db, publication_id, user_id)
    snapshot = MetricSnapshot(publication_id=publication_id, **payload.model_dump())
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get(
    "/publications/{publication_id}/milestones",
    response_model=list[PerformanceMilestone],
)
def publication_milestones(
    publication_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[PerformanceMilestone]:
    publication = _get_owned_publication(db, publication_id, user_id)
    snapshots = list(
        db.scalars(
            select(MetricSnapshot)
            .where(MetricSnapshot.publication_id == publication_id)
            .order_by(MetricSnapshot.captured_at.asc())
        )
    )

    result: list[PerformanceMilestone] = []
    for label, target_hours in MILESTONES:
        target_at = (
            publication.published_at + timedelta(hours=target_hours)
            if publication.published_at is not None
            else None
        )
        snapshot = None
        if target_at is not None:
            snapshot = next(
                (item for item in snapshots if item.captured_at >= target_at),
                None,
            )

        result.append(
            PerformanceMilestone(
                label=label,
                target_hours=target_hours,
                target_at=target_at,
                captured_at=snapshot.captured_at if snapshot else None,
                views=snapshot.views if snapshot else None,
                likes=snapshot.likes if snapshot else None,
                comments=snapshot.comments if snapshot else None,
                favorites=snapshot.favorites if snapshot else None,
                shares=snapshot.shares if snapshot else None,
                followers_gained=snapshot.followers_gained if snapshot else None,
            )
        )
    return result


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> AnalyticsSummary:
    latest = _latest_metric_snapshot_subquery()
    row = db.execute(
        select(
            func.count(latest.c.id),
            func.coalesce(func.sum(latest.c.views), 0),
            func.coalesce(func.sum(latest.c.likes), 0),
            func.coalesce(func.sum(latest.c.comments), 0),
            func.coalesce(func.sum(latest.c.favorites), 0),
            func.coalesce(func.sum(latest.c.shares), 0),
            func.coalesce(func.sum(latest.c.followers_gained), 0),
        )
        .select_from(latest)
        .join(Publication, Publication.id == latest.c.publication_id)
        .join(Content, Content.id == Publication.content_id)
        .where(Content.user_id == user_id)
    ).one()
    publications, views, likes, comments, favorites, shares, followers = [
        int(value) for value in row
    ]
    interactions = likes + comments + favorites + shares
    engagement_rate = round((interactions / views * 100) if views else 0.0, 2)
    return AnalyticsSummary(
        publications=publications,
        views=views,
        likes=likes,
        comments=comments,
        favorites=favorites,
        shares=shares,
        followers_gained=followers,
        engagement_rate=engagement_rate,
    )


@router.get("/pillars", response_model=list[PillarAnalyticsItem])
def analytics_by_pillar(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[PillarAnalyticsItem]:
    latest = _latest_metric_snapshot_subquery()
    rows = db.execute(
        select(
            ContentPillar.id,
            ContentPillar.name,
            func.count(latest.c.id).label("publications"),
            func.coalesce(func.sum(latest.c.views), 0).label("views"),
            func.coalesce(func.sum(latest.c.likes), 0).label("likes"),
            func.coalesce(func.sum(latest.c.comments), 0).label("comments"),
            func.coalesce(func.sum(latest.c.favorites), 0).label("favorites"),
            func.coalesce(func.sum(latest.c.shares), 0).label("shares"),
            func.coalesce(func.sum(latest.c.followers_gained), 0).label("followers"),
        )
        .select_from(ContentPillar)
        .join(Content, Content.pillar_id == ContentPillar.id)
        .join(Publication, Publication.content_id == Content.id)
        .join(latest, latest.c.publication_id == Publication.id)
        .where(ContentPillar.user_id == user_id)
        .group_by(ContentPillar.id, ContentPillar.name)
        .order_by(func.sum(latest.c.views).desc())
    ).all()

    result: list[PillarAnalyticsItem] = []
    for row in rows:
        publications = int(row.publications)
        views = int(row.views)
        likes = int(row.likes)
        comments = int(row.comments)
        favorites = int(row.favorites)
        shares = int(row.shares)
        followers = int(row.followers)
        avg_views, engagement_rate, favorite_rate, follower_conversion_rate = _rates(
            publications,
            views,
            likes,
            comments,
            favorites,
            shares,
            followers,
        )
        result.append(
            PillarAnalyticsItem(
                pillar_id=row.id,
                pillar_name=row.name,
                publications=publications,
                views=views,
                likes=likes,
                comments=comments,
                favorites=favorites,
                shares=shares,
                followers_gained=followers,
                avg_views=avg_views,
                engagement_rate=engagement_rate,
                favorite_rate=favorite_rate,
                follower_conversion_rate=follower_conversion_rate,
            )
        )
    return result


def _pillar_period_rows(
    db: Session,
    user_id: UUID,
    start_at: datetime,
    end_at: datetime,
) -> dict[UUID, dict[str, int | str]]:
    latest = _latest_metric_snapshot_subquery()
    rows = db.execute(
        select(
            ContentPillar.id,
            ContentPillar.name,
            func.count(latest.c.id).label("publications"),
            func.coalesce(func.sum(latest.c.views), 0).label("views"),
            func.coalesce(func.sum(latest.c.favorites), 0).label("favorites"),
        )
        .select_from(ContentPillar)
        .join(Content, Content.pillar_id == ContentPillar.id)
        .join(Publication, Publication.content_id == Content.id)
        .join(latest, latest.c.publication_id == Publication.id)
        .where(
            ContentPillar.user_id == user_id,
            Publication.published_at.is_not(None),
            Publication.published_at >= start_at,
            Publication.published_at < end_at,
        )
        .group_by(ContentPillar.id, ContentPillar.name)
    ).all()
    return {
        row.id: {
            "name": row.name,
            "publications": int(row.publications),
            "views": int(row.views),
            "favorites": int(row.favorites),
        }
        for row in rows
    }


@router.get("/pillar-trends", response_model=list[PillarTrendItem])
def analytics_pillar_trends(
    window_days: int = Query(default=30, ge=7, le=180),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[PillarTrendItem]:
    now = datetime.now(timezone.utc)
    recent_start = now - timedelta(days=window_days)
    previous_start = recent_start - timedelta(days=window_days)
    recent = _pillar_period_rows(db, user_id, recent_start, now)
    previous = _pillar_period_rows(db, user_id, previous_start, recent_start)

    result: list[PillarTrendItem] = []
    for pillar_id in set(recent) | set(previous):
        recent_row = recent.get(pillar_id, {})
        previous_row = previous.get(pillar_id, {})
        name = str(recent_row.get("name") or previous_row.get("name") or "Unnamed")
        recent_publications = int(recent_row.get("publications", 0))
        previous_publications = int(previous_row.get("publications", 0))
        recent_views = int(recent_row.get("views", 0))
        previous_views = int(previous_row.get("views", 0))
        recent_favorites = int(recent_row.get("favorites", 0))
        previous_favorites = int(previous_row.get("favorites", 0))
        recent_avg_views = round(recent_views / recent_publications, 2) if recent_publications else 0.0
        previous_avg_views = (
            round(previous_views / previous_publications, 2) if previous_publications else 0.0
        )
        recent_favorite_rate = (
            round(recent_favorites / recent_views * 100, 2) if recent_views else 0.0
        )
        previous_favorite_rate = (
            round(previous_favorites / previous_views * 100, 2) if previous_views else 0.0
        )

        view_change_percent: float | None = None
        if previous_avg_views > 0:
            view_change_percent = round(
                (recent_avg_views - previous_avg_views) / previous_avg_views * 100,
                2,
            )

        if previous_publications == 0 and recent_publications > 0:
            signal = "new"
        elif recent_publications == 0:
            signal = "falling" if previous_publications > 0 else "insufficient"
        elif previous_publications == 0 or view_change_percent is None:
            signal = "insufficient"
        elif view_change_percent >= 20:
            signal = "rising"
        elif view_change_percent <= -20:
            signal = "falling"
        else:
            signal = "stable"

        result.append(
            PillarTrendItem(
                pillar_id=pillar_id,
                pillar_name=name,
                recent_publications=recent_publications,
                previous_publications=previous_publications,
                recent_avg_views=recent_avg_views,
                previous_avg_views=previous_avg_views,
                view_change_percent=view_change_percent,
                recent_favorite_rate=recent_favorite_rate,
                previous_favorite_rate=previous_favorite_rate,
                signal=signal,
            )
        )

    signal_order = {"rising": 0, "new": 1, "stable": 2, "insufficient": 3, "falling": 4}
    result.sort(key=lambda item: (signal_order[item.signal], -item.recent_avg_views, item.pillar_name))
    return result


@router.get("/platforms", response_model=list[PlatformAnalyticsItem])
def analytics_by_platform(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[PlatformAnalyticsItem]:
    latest = _latest_metric_snapshot_subquery()
    rows = db.execute(
        select(
            Platform.id,
            Platform.slug,
            Platform.name,
            func.count(latest.c.id).label("publications"),
            func.coalesce(func.sum(latest.c.views), 0).label("views"),
            func.coalesce(func.sum(latest.c.likes), 0).label("likes"),
            func.coalesce(func.sum(latest.c.comments), 0).label("comments"),
            func.coalesce(func.sum(latest.c.favorites), 0).label("favorites"),
            func.coalesce(func.sum(latest.c.shares), 0).label("shares"),
            func.coalesce(func.sum(latest.c.followers_gained), 0).label("followers"),
        )
        .select_from(Platform)
        .join(PlatformAccount, PlatformAccount.platform_id == Platform.id)
        .join(Publication, Publication.platform_account_id == PlatformAccount.id)
        .join(Content, Content.id == Publication.content_id)
        .join(latest, latest.c.publication_id == Publication.id)
        .where(Content.user_id == user_id, PlatformAccount.user_id == user_id)
        .group_by(Platform.id, Platform.slug, Platform.name)
        .order_by(func.sum(latest.c.views).desc())
    ).all()

    result: list[PlatformAnalyticsItem] = []
    for row in rows:
        publications = int(row.publications)
        views = int(row.views)
        likes = int(row.likes)
        comments = int(row.comments)
        favorites = int(row.favorites)
        shares = int(row.shares)
        followers = int(row.followers)
        avg_views, engagement_rate, favorite_rate, follower_conversion_rate = _rates(
            publications,
            views,
            likes,
            comments,
            favorites,
            shares,
            followers,
        )
        result.append(
            PlatformAnalyticsItem(
                platform_id=row.id,
                platform_slug=row.slug,
                platform_name=row.name,
                publications=publications,
                views=views,
                likes=likes,
                comments=comments,
                favorites=favorites,
                shares=shares,
                followers_gained=followers,
                avg_views=avg_views,
                engagement_rate=engagement_rate,
                favorite_rate=favorite_rate,
                follower_conversion_rate=follower_conversion_rate,
            )
        )
    return result


@router.get("/tags", response_model=list[TagAnalyticsItem])
def analytics_by_tag(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[TagAnalyticsItem]:
    latest = _latest_metric_snapshot_subquery()
    rows = db.execute(
        select(
            Tag.id,
            Tag.name,
            func.count(func.distinct(Content.id)).label("contents"),
            func.count(latest.c.id).label("publications"),
            func.coalesce(func.sum(latest.c.views), 0).label("views"),
            func.coalesce(func.sum(latest.c.likes), 0).label("likes"),
            func.coalesce(func.sum(latest.c.comments), 0).label("comments"),
            func.coalesce(func.sum(latest.c.favorites), 0).label("favorites"),
            func.coalesce(func.sum(latest.c.shares), 0).label("shares"),
            func.coalesce(func.sum(latest.c.followers_gained), 0).label("followers"),
        )
        .select_from(Tag)
        .join(content_tags, content_tags.c.tag_id == Tag.id)
        .join(Content, Content.id == content_tags.c.content_id)
        .join(Publication, Publication.content_id == Content.id)
        .join(latest, latest.c.publication_id == Publication.id)
        .where(Tag.user_id == user_id, Content.user_id == user_id)
        .group_by(Tag.id, Tag.name)
        .order_by(func.sum(latest.c.views).desc())
    ).all()

    result: list[TagAnalyticsItem] = []
    for row in rows:
        publications = int(row.publications)
        views = int(row.views)
        likes = int(row.likes)
        comments = int(row.comments)
        favorites = int(row.favorites)
        shares = int(row.shares)
        followers = int(row.followers)
        avg_views, engagement_rate, favorite_rate, follower_conversion_rate = _rates(
            publications,
            views,
            likes,
            comments,
            favorites,
            shares,
            followers,
        )
        result.append(
            TagAnalyticsItem(
                tag_id=row.id,
                tag_name=row.name,
                contents=int(row.contents),
                publications=publications,
                views=views,
                likes=likes,
                comments=comments,
                favorites=favorites,
                shares=shares,
                followers_gained=followers,
                avg_views=avg_views,
                engagement_rate=engagement_rate,
                favorite_rate=favorite_rate,
                follower_conversion_rate=follower_conversion_rate,
            )
        )
    return result
