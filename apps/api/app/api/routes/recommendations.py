from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.schemas_recommendations import TopicRecommendation
from app.services.recommendations import rank_topics

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/topics", response_model=list[TopicRecommendation])
def topic_recommendations(
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[TopicRecommendation]:
    return rank_topics(db, user_id=user_id, limit=limit)
