from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, Inspiration, Publication, Topic
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> DashboardSummary:
    inspirations_inbox = db.scalar(
        select(func.count())
        .select_from(Inspiration)
        .where(Inspiration.user_id == user_id, Inspiration.status == "inbox")
    )
    topics_approved = db.scalar(
        select(func.count())
        .select_from(Topic)
        .where(Topic.user_id == user_id, Topic.status == "approved")
    )
    contents_in_progress = db.scalar(
        select(func.count())
        .select_from(Content)
        .where(
            Content.user_id == user_id,
            Content.status.in_(["research", "outline", "script", "shooting", "editing", "ready"]),
        )
    )
    publications_scheduled = db.scalar(
        select(func.count())
        .select_from(Publication)
        .join(Content, Content.id == Publication.content_id)
        .where(Content.user_id == user_id, Publication.status == "scheduled")
    )
    contents_to_review = db.scalar(
        select(func.count())
        .select_from(Content)
        .where(Content.user_id == user_id, Content.status == "review")
    )
    return DashboardSummary(
        inspirations_inbox=int(inspirations_inbox or 0),
        topics_approved=int(topics_approved or 0),
        contents_in_progress=int(contents_in_progress or 0),
        publications_scheduled=int(publications_scheduled or 0),
        contents_to_review=int(contents_to_review or 0),
    )
