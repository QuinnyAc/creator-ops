from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, Review
from app.schemas import ReviewRead, ReviewUpsert

router = APIRouter(prefix="/reviews", tags=["reviews"])


def _ensure_owned_content(db: Session, content_id: UUID, user_id: UUID) -> None:
    owned = db.scalar(
        select(Content.id).where(Content.id == content_id, Content.user_id == user_id)
    )
    if owned is None:
        raise HTTPException(status_code=404, detail="Content not found.")


@router.get("/content/{content_id}", response_model=ReviewRead)
def get_review(
    content_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Review:
    _ensure_owned_content(db, content_id, user_id)
    review = db.scalar(select(Review).where(Review.content_id == content_id))
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found.")
    return review


@router.put("/content/{content_id}", response_model=ReviewRead)
def upsert_review(
    content_id: UUID,
    payload: ReviewUpsert,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Review:
    _ensure_owned_content(db, content_id, user_id)
    review = db.scalar(select(Review).where(Review.content_id == content_id))
    if review is None:
        review = Review(content_id=content_id)
        db.add(review)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(review, key, value)
    db.commit()
    db.refresh(review)
    return review
