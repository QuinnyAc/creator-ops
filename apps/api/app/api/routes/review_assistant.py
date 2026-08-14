from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content
from app.schemas_review_assistant import ReviewSuggestion
from app.services.review_assistant import build_review_suggestion

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/content/{content_id}/suggestions", response_model=ReviewSuggestion)
def get_review_suggestions(
    content_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> ReviewSuggestion:
    content = db.scalar(
        select(Content).where(Content.id == content_id, Content.user_id == user_id)
    )
    if content is None:
        raise HTTPException(status_code=404, detail="Content not found.")
    return build_review_suggestion(db, content=content, user_id=user_id)
