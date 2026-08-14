from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import ContentPillar, Tag
from app.schemas import (
    ContentPillarCreate,
    ContentPillarRead,
    ContentPillarUpdate,
    TagCreate,
    TagRead,
)

router = APIRouter(tags=["settings"])


@router.get("/content-pillars", response_model=list[ContentPillarRead])
def list_content_pillars(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[ContentPillar]:
    return list(
        db.scalars(
            select(ContentPillar)
            .where(ContentPillar.user_id == user_id)
            .order_by(ContentPillar.name)
        )
    )


@router.post(
    "/content-pillars",
    response_model=ContentPillarRead,
    status_code=status.HTTP_201_CREATED,
)
def create_content_pillar(
    payload: ContentPillarCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> ContentPillar:
    pillar = ContentPillar(user_id=user_id, **payload.model_dump())
    db.add(pillar)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Content pillar name already exists.") from exc
    db.refresh(pillar)
    return pillar


@router.patch("/content-pillars/{pillar_id}", response_model=ContentPillarRead)
def update_content_pillar(
    pillar_id: UUID,
    payload: ContentPillarUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> ContentPillar:
    pillar = db.scalar(
        select(ContentPillar).where(
            ContentPillar.id == pillar_id,
            ContentPillar.user_id == user_id,
        )
    )
    if pillar is None:
        raise HTTPException(status_code=404, detail="Content pillar not found.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(pillar, key, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Content pillar name already exists.") from exc
    db.refresh(pillar)
    return pillar


@router.delete("/content-pillars/{pillar_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_content_pillar(
    pillar_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    pillar = db.scalar(
        select(ContentPillar).where(
            ContentPillar.id == pillar_id,
            ContentPillar.user_id == user_id,
        )
    )
    if pillar is None:
        raise HTTPException(status_code=404, detail="Content pillar not found.")
    db.delete(pillar)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/tags", response_model=list[TagRead])
def list_tags(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Tag]:
    return list(
        db.scalars(select(Tag).where(Tag.user_id == user_id).order_by(Tag.name))
    )


@router.post("/tags", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Tag:
    tag = Tag(user_id=user_id, **payload.model_dump())
    db.add(tag)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Tag name already exists.") from exc
    db.refresh(tag)
    return tag


@router.delete("/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    tag = db.scalar(select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id))
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found.")
    db.delete(tag)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
