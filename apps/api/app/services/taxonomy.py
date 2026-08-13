from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Tag


def get_owned_tags(db: Session, tag_ids: list[UUID], user_id: UUID) -> list[Tag]:
    unique_ids = list(dict.fromkeys(tag_ids))
    if not unique_ids:
        return []

    tags = list(
        db.scalars(
            select(Tag)
            .where(Tag.user_id == user_id, Tag.id.in_(unique_ids))
            .order_by(Tag.name)
        )
    )
    if len(tags) != len(unique_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more tags do not belong to the current user.",
        )
    return tags
