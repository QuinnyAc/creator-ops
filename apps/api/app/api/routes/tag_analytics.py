from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, MetricSnapshot, Publication, Tag, content_tags
from app.schemas_analytics import TagAnalyticsItem

router = APIRouter(prefix="/analytics/tags", tags=["analytics"])


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


@router.get("", response_model=list[TagAnalyticsItem])
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
        .order_by(func.sum(latest.c.views).desc(), Tag.name.asc())
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
