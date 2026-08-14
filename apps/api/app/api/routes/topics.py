from collections import defaultdict
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, insert, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import ContentPillar, Tag, Topic, TopicScore, topic_tags
from app.schemas import (
    TagRead,
    TopicCreate,
    TopicRead,
    TopicScoreInput,
    TopicScoreRead,
    TopicUpdate,
)
from app.schemas_taxonomy import TagAssignment, TopicLibraryItem
from app.services.scoring import calculate_topic_scores
from app.services.taxonomy import get_owned_tags

router = APIRouter(prefix="/topics", tags=["topics"])


def _get_owned(db: Session, topic_id: UUID, user_id: UUID) -> Topic:
    item = db.scalar(select(Topic).where(Topic.id == topic_id, Topic.user_id == user_id))
    if item is None:
        raise HTTPException(status_code=404, detail="Topic not found.")
    return item


def _validate_pillar(db: Session, pillar_id: UUID | None, user_id: UUID) -> None:
    if pillar_id is None:
        return
    exists = db.scalar(
        select(ContentPillar.id).where(
            ContentPillar.id == pillar_id,
            ContentPillar.user_id == user_id,
        )
    )
    if exists is None:
        raise HTTPException(status_code=400, detail="Content pillar does not belong to user.")


@router.get("", response_model=list[TopicLibraryItem])
def list_topics(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[TopicLibraryItem]:
    rows = db.execute(
        select(Topic, TopicScore)
        .outerjoin(TopicScore, TopicScore.topic_id == Topic.id)
        .where(Topic.user_id == user_id)
        .order_by(Topic.created_at.desc())
    ).all()

    tags_by_topic: dict[UUID, list[TagRead]] = defaultdict(list)
    tag_rows = db.execute(
        select(topic_tags.c.topic_id, Tag)
        .join(Tag, Tag.id == topic_tags.c.tag_id)
        .join(Topic, Topic.id == topic_tags.c.topic_id)
        .where(Topic.user_id == user_id, Tag.user_id == user_id)
        .order_by(Tag.name)
    ).all()
    for topic_id, tag in tag_rows:
        tags_by_topic[topic_id].append(TagRead.model_validate(tag))

    return [
        TopicLibraryItem(
            **TopicRead.model_validate(topic).model_dump(),
            opportunity_score=score.opportunity_score if score else None,
            priority_score=score.priority_score if score else None,
            tags=tags_by_topic.get(topic.id, []),
        )
        for topic, score in rows
    ]


@router.post("", response_model=TopicRead, status_code=status.HTTP_201_CREATED)
def create_topic(
    payload: TopicCreate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Topic:
    _validate_pillar(db, payload.pillar_id, user_id)
    item = Topic(user_id=user_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{topic_id}", response_model=TopicRead)
def get_topic(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Topic:
    return _get_owned(db, topic_id, user_id)


@router.patch("/{topic_id}", response_model=TopicRead)
def update_topic(
    topic_id: UUID,
    payload: TopicUpdate,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Topic:
    item = _get_owned(db, topic_id, user_id)
    changes = payload.model_dump(exclude_unset=True)
    if "pillar_id" in changes:
        _validate_pillar(db, changes["pillar_id"], user_id)
    for key, value in changes.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_topic(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    item = _get_owned(db, topic_id, user_id)
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{topic_id}/tags", response_model=list[TagRead])
def list_topic_tags(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Tag]:
    _get_owned(db, topic_id, user_id)
    return list(
        db.scalars(
            select(Tag)
            .join(topic_tags, topic_tags.c.tag_id == Tag.id)
            .where(topic_tags.c.topic_id == topic_id, Tag.user_id == user_id)
            .order_by(Tag.name)
        )
    )


@router.put("/{topic_id}/tags", response_model=list[TagRead])
def replace_topic_tags(
    topic_id: UUID,
    payload: TagAssignment,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> list[Tag]:
    _get_owned(db, topic_id, user_id)
    tags = get_owned_tags(db, payload.tag_ids, user_id)
    db.execute(delete(topic_tags).where(topic_tags.c.topic_id == topic_id))
    if tags:
        db.execute(
            insert(topic_tags),
            [{"topic_id": topic_id, "tag_id": tag.id} for tag in tags],
        )
    db.commit()
    return tags


@router.put("/{topic_id}/score", response_model=TopicScoreRead)
def score_topic(
    topic_id: UUID,
    payload: TopicScoreInput,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> TopicScore:
    _get_owned(db, topic_id, user_id)
    opportunity, priority = calculate_topic_scores(**payload.model_dump())
    score = db.scalar(select(TopicScore).where(TopicScore.topic_id == topic_id))
    if score is None:
        score = TopicScore(topic_id=topic_id, **payload.model_dump())
        db.add(score)
    else:
        for key, value in payload.model_dump().items():
            setattr(score, key, value)

    score.opportunity_score = opportunity
    score.priority_score = priority
    db.commit()
    db.refresh(score)
    return score


@router.get("/{topic_id}/score", response_model=TopicScoreRead)
def get_topic_score(
    topic_id: UUID,
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> TopicScore:
    _get_owned(db, topic_id, user_id)
    score = db.scalar(select(TopicScore).where(TopicScore.topic_id == topic_id))
    if score is None:
        raise HTTPException(status_code=404, detail="Topic has not been scored.")
    return score
