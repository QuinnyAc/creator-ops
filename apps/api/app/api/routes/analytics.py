from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, MetricSnapshot, Publication
from app.schemas import AnalyticsSummary, MetricSnapshotCreate, MetricSnapshotRead

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _ensure_owned_publication(db: Session, publication_id: UUID, user_id: UUID) -> None:
    owned = db.scalar(
        select(Publication.id)
        .join(Content, Content.id == Publication.content_id)
        .where(Publication.id == publication_id, Content.user_id == user_id)
    )
    if owned is None:
        raise HTTPException(status_code=404, detail="Publication not found.")


@router.get("/publications/{publication_id}/metrics", response_model=list[MetricSnapshotRead])
def list_metrics(
    publication_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[MetricSnapshot]:
    _ensure_owned_publication(db, publication_id, user_id)
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
    _ensure_owned_publication(db, publication_id, user_id)
    snapshot = MetricSnapshot(publication_id=publication_id, **payload.model_dump())
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> AnalyticsSummary:
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
