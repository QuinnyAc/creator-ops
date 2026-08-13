from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Content, ContentPillar, Tag, Topic, content_tags
from app.schemas import ContentCreate, ContentRead, ContentUpdate, TagRead
from app.schemas_taxonomy import TagAssignment
from app.services.taxonomy import get_owned_tags

router = APIRouter(prefix="/contents", tags=["contents"])


def _get_owned(db: Session, content_id: UUID, user_id: UUID) -> Content:
    item = db.scalar(
        select(Content).where(Content.id == content_id, Content.user_id == user_id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Content not found.")
    return item


def _validate_links(
    db: Session,
    user_id: UUID,
    topic_id: UUID | None,
    pillar_id: UUID | None,
) -> None:
    if topic_id is not None:
        topic = db.scalar(
            select(Topic.id).where(Topic.id == topic_id, Topic.user_id == user_id)
        )
        if topic is None:
            raise HTTPException(status_code=400, detail="Topic does not belong to user.")
    if pillar_id is not None:
        pillar = db.scalar(
            select(ContentPillar.id).where(
                ContentPillar.id == pillar_id,
                ContentPillar.user_id == user_id,
            )
        )
        if pillar is None:
            raise HTTPException(
                status_code=400,
                detail="Content pillar does not belong to user.",
            )


@router.get("", response_model=list[ContentRead])
def list_contents(
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Content]:
    stmt = select(Content).where(Content.user_id == user_id)
    if status_filter:
        stmt = stmt.where(Content.status == status_filter)
    return list(db.scalars(stmt.order_by(Content.created_at.desc())))


@router.post("", response_model=ContentRead, status_code=status.HTTP_201_CREATED)
def create_content(
    payload: ContentCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Content:
    _validate_links(db, user_id, payload.topic_id, payload.pillar_id)
    item = Content(user_id=user_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{content_id}", response_model=ContentRead)
def get_content(
    content_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Content:
    return _get_owned(db, content_id, user_id)


@router.patch("/{content_id}", response_model=ContentRead)
def update_content(
    content_id: UUID,
    payload: ContentUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Content:
    item = _get_owned(db, content_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    _validate_links(
        db,
        user_id,
        changes.get("topic_id", item.topic_id),
        changes.get("pillar_id", item.pillar_id),
    )
    for key, value in changes.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{content_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content(
    content_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    item = _get_owned(db, content_id, user_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{content_id}/tags", response_model=list[TagRead])
def list_content_tags(
    content_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Tag]:
    _get_owned(db, content_id, user_id)
    return list(
        db.scalars(
            select(Tag)
            .join(content_tags, content_tags.c.tag_id == Tag.id)
            .where(content_tags.c.content_id == content_id, Tag.user_id == user_id)
            .order_by(Tag.name)
        )
    )


@router.put("/{content_id}/tags", response_model=list[TagRead])
def replace_content_tags(
    content_id: UUID,
    payload: TagAssignment,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Tag]:
    _get_owned(db, content_id, user_id)
    tags = get_owned_tags(db, payload.tag_ids, user_id)
    db.execute(delete(content_tags).where(content_tags.c.content_id == content_id))
    if tags:
        db.execute(
            insert(content_tags),
            [{"content_id": content_id, "tag_id": tag.id} for tag in tags],
        )
    db.commit()
    return tags
