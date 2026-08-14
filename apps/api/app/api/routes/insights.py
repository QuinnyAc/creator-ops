from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, Review
from app.models_insights import Insight
from app.schemas_insights import InsightCreate, InsightPromoteRequest, InsightRead, InsightUpdate

router = APIRouter(prefix="/insights", tags=["insights"])


def _get_owned_insight(db: Session, insight_id: UUID, user_id: UUID) -> Insight:
    insight = db.scalar(
        select(Insight).where(Insight.id == insight_id, Insight.user_id == user_id)
    )
    if insight is None:
        raise HTTPException(status_code=404, detail="Insight not found.")
    return insight


@router.get("", response_model=list[InsightRead])
def list_insights(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Insight]:
    query = select(Insight).where(Insight.user_id == user_id)
    if status_filter:
        query = query.where(Insight.status == status_filter)
    return list(db.scalars(query.order_by(Insight.updated_at.desc())))


@router.post("", response_model=InsightRead, status_code=status.HTTP_201_CREATED)
def create_insight(
    payload: InsightCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Insight:
    insight = Insight(user_id=user_id, **payload.model_dump())
    db.add(insight)
    db.commit()
    db.refresh(insight)
    return insight


@router.post("/from-content/{content_id}", response_model=InsightRead)
def promote_review_learning(
    content_id: UUID,
    payload: InsightPromoteRequest,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Insight:
    row = db.execute(
        select(Review, Content.title.label("content_title"))
        .join(Content, Content.id == Review.content_id)
        .where(Review.content_id == content_id, Content.user_id == user_id)
    ).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Review not found for this content.")
    if not row.Review.learnings or not row.Review.learnings.strip():
        raise HTTPException(status_code=400, detail="Add review learnings before promoting an insight.")

    insight = db.scalar(
        select(Insight).where(
            Insight.user_id == user_id,
            Insight.source_review_id == row.Review.id,
        )
    )
    if insight is None:
        insight = Insight(
            user_id=user_id,
            source_review_id=row.Review.id,
            title=payload.title or row.content_title,
            body=row.Review.learnings.strip(),
            category=payload.category,
        )
        db.add(insight)
    else:
        insight.title = payload.title or row.content_title
        insight.body = row.Review.learnings.strip()
        insight.category = payload.category
        insight.status = "active"

    db.commit()
    db.refresh(insight)
    return insight


@router.patch("/{insight_id}", response_model=InsightRead)
def update_insight(
    insight_id: UUID,
    payload: InsightUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Insight:
    insight = _get_owned_insight(db, insight_id, user_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(insight, key, value)
    db.commit()
    db.refresh(insight)
    return insight


@router.delete("/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insight(
    insight_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    insight = _get_owned_insight(db, insight_id, user_id)
    db.delete(insight)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
