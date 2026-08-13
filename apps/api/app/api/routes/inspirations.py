from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import Inspiration, Topic
from app.schemas import (
    InspirationConvertRequest,
    InspirationCreate,
    InspirationRead,
    InspirationUpdate,
    TopicRead,
)

router = APIRouter(prefix="/inspirations", tags=["inspirations"])


def _get_owned(db: Session, inspiration_id: UUID, user_id: UUID) -> Inspiration:
    item = db.scalar(
        select(Inspiration).where(
            Inspiration.id == inspiration_id,
            Inspiration.user_id == user_id,
        )
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Inspiration not found.")
    return item


@router.get("", response_model=list[InspirationRead])
def list_inspirations(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Inspiration]:
    return list(
        db.scalars(
            select(Inspiration)
            .where(Inspiration.user_id == user_id)
            .order_by(Inspiration.created_at.desc())
        )
    )


@router.post("", response_model=InspirationRead, status_code=status.HTTP_201_CREATED)
def create_inspiration(
    payload: InspirationCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Inspiration:
    item = Inspiration(user_id=user_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{inspiration_id}", response_model=InspirationRead)
def get_inspiration(
    inspiration_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Inspiration:
    return _get_owned(db, inspiration_id, user_id)


@router.patch("/{inspiration_id}", response_model=InspirationRead)
def update_inspiration(
    inspiration_id: UUID,
    payload: InspirationUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Inspiration:
    item = _get_owned(db, inspiration_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(item, key, value)
    if changes.get("status") == "archived":
        item.archived_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{inspiration_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inspiration(
    inspiration_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    item = _get_owned(db, inspiration_id, user_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{inspiration_id}/convert", response_model=TopicRead, status_code=201)
def convert_inspiration(
    inspiration_id: UUID,
    payload: InspirationConvertRequest,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Topic:
    item = _get_owned(db, inspiration_id, user_id)
    topic = Topic(
        user_id=user_id,
        inspiration_id=item.id,
        title=payload.title or item.title,
        pillar_id=payload.pillar_id,
        core_idea=payload.core_idea or item.note,
        target_audience=payload.target_audience,
        user_problem=payload.user_problem,
        angle=payload.angle,
        goal=payload.goal,
        planned_platforms=payload.planned_platforms,
        status="evaluating",
    )
    item.status = "converted"
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic
