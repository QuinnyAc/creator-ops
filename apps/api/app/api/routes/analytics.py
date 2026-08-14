from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
)
from app.schemas import AnalyticsSummary, MetricSnapshotCreate, MetricSnapshotRead
from app.schemas_analytics import PerformanceMilestone, PillarAnalyticsItem, PlatformAnalyticsItem

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
