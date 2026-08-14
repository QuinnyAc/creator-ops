import csv
from io import StringIO
from uuid import UUID

from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_id
from app.db import get_db
from app.models import (
    Content,
    ContentPillar,
    MetricSnapshot,
    Platform,
    PlatformAccount,
    Publication,
    Review,
    Topic,
    TopicScore,
)

router = APIRouter(prefix="/exports", tags=["exports"])


def _value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    return str(value)


def _csv_response(filename: str, headers: list[str], rows: list[list[object]]) -> Response:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_value(value) for value in row])

    # UTF-8 BOM keeps Chinese headers/content readable when opened directly in Excel.
    content = "\ufeff" + buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _latest_metric_snapshot_subquery():
    latest_times = (
        select(
            MetricSnapshot.publication_id,
            func.max(MetricSnapshot.captured_at).label("captured_at"),
        )
        .group_by(MetricSnapshot.publication_id)
        .subquery()
    )
    return (
        select(MetricSnapshot)
        .join(
            latest_times,
            (MetricSnapshot.publication_id == latest_times.c.publication_id)
            & (MetricSnapshot.captured_at == latest_times.c.captured_at),
        )
        .subquery()
    )


@router.get("/topics.csv")
def export_topics(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    rows = db.execute(
        select(
            Topic,
            TopicScore,
            ContentPillar.name.label("pillar_name"),
        )
        .outerjoin(TopicScore, TopicScore.topic_id == Topic.id)
        .outerjoin(ContentPillar, ContentPillar.id == Topic.pillar_id)
        .where(Topic.user_id == user_id)
        .order_by(Topic.created_at.desc())
    ).all()

    return _csv_response(
        "creator-ops-topics.csv",
        [
            "id",
            "title",
            "status",
            "pillar",
            "goal",
            "planned_platforms",
            "core_idea",
            "target_audience",
            "user_problem",
            "angle",
            "pain_point",
            "search_demand",
            "trend_heat",
            "differentiation",
            "commercial_value",
            "production_effort",
            "opportunity_score",
            "priority_score",
            "created_at",
            "updated_at",
        ],
        [
            [
                row.Topic.id,
                row.Topic.title,
                row.Topic.status,
                row.pillar_name,
                row.Topic.goal,
                row.Topic.planned_platforms,
                row.Topic.core_idea,
                row.Topic.target_audience,
                row.Topic.user_problem,
                row.Topic.angle,
                row.TopicScore.pain_point if row.TopicScore else None,
                row.TopicScore.search_demand if row.TopicScore else None,
                row.TopicScore.trend_heat if row.TopicScore else None,
                row.TopicScore.differentiation if row.TopicScore else None,
                row.TopicScore.commercial_value if row.TopicScore else None,
                row.TopicScore.production_effort if row.TopicScore else None,
                row.TopicScore.opportunity_score if row.TopicScore else None,
                row.TopicScore.priority_score if row.TopicScore else None,
                row.Topic.created_at,
                row.Topic.updated_at,
            ]
            for row in rows
        ],
    )


@router.get("/contents.csv")
def export_contents(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    rows = db.execute(
        select(
            Content,
            Topic.title.label("topic_title"),
            ContentPillar.name.label("pillar_name"),
        )
        .outerjoin(Topic, Topic.id == Content.topic_id)
        .outerjoin(ContentPillar, ContentPillar.id == Content.pillar_id)
        .where(Content.user_id == user_id)
        .order_by(Content.created_at.desc())
    ).all()

    return _csv_response(
        "creator-ops-contents.csv",
        [
            "id",
            "title",
            "content_type",
            "status",
            "topic",
            "pillar",
            "planned_publish_at",
            "research_notes",
            "outline",
            "script",
            "copywriting",
            "cta",
            "created_at",
            "updated_at",
        ],
        [
            [
                row.Content.id,
                row.Content.title,
                row.Content.content_type,
                row.Content.status,
                row.topic_title,
                row.pillar_name,
                row.Content.planned_publish_at,
                row.Content.research_notes,
                row.Content.outline,
                row.Content.script,
                row.Content.copywriting,
                row.Content.cta,
                row.Content.created_at,
                row.Content.updated_at,
            ]
            for row in rows
        ],
    )


@router.get("/publications.csv")
def export_publications(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    latest = _latest_metric_snapshot_subquery()
    rows = db.execute(
        select(
            Publication,
            Content.title.label("content_title"),
            Platform.name.label("platform_name"),
            Platform.slug.label("platform_slug"),
            PlatformAccount.name.label("account_name"),
            PlatformAccount.handle.label("account_handle"),
            latest.c.captured_at,
            latest.c.views,
            latest.c.likes,
            latest.c.comments,
            latest.c.favorites,
            latest.c.shares,
            latest.c.followers_gained,
        )
        .join(Content, Content.id == Publication.content_id)
        .join(PlatformAccount, PlatformAccount.id == Publication.platform_account_id)
        .join(Platform, Platform.id == PlatformAccount.platform_id)
        .outerjoin(latest, latest.c.publication_id == Publication.id)
        .where(Content.user_id == user_id, PlatformAccount.user_id == user_id)
        .order_by(Publication.created_at.desc())
    ).all()

    return _csv_response(
        "creator-ops-publications.csv",
        [
            "id",
            "content",
            "platform",
            "platform_slug",
            "account",
            "account_handle",
            "title",
            "status",
            "scheduled_at",
            "published_at",
            "url",
            "platform_tags",
            "latest_captured_at",
            "views",
            "likes",
            "favorites",
            "comments",
            "shares",
            "followers_gained",
            "created_at",
            "updated_at",
        ],
        [
            [
                row.Publication.id,
                row.content_title,
                row.platform_name,
                row.platform_slug,
                row.account_name,
                row.account_handle,
                row.Publication.title,
                row.Publication.status,
                row.Publication.scheduled_at,
                row.Publication.published_at,
                row.Publication.url,
                row.Publication.platform_tags,
                row.captured_at,
                row.views,
                row.likes,
                row.favorites,
                row.comments,
                row.shares,
                row.followers_gained,
                row.Publication.created_at,
                row.Publication.updated_at,
            ]
            for row in rows
        ],
    )


@router.get("/reviews.csv")
def export_reviews(
    db: Session = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> Response:
    rows = db.execute(
        select(Review, Content.title.label("content_title"))
        .join(Content, Content.id == Review.content_id)
        .where(Content.user_id == user_id)
        .order_by(Review.updated_at.desc())
    ).all()

    return _csv_response(
        "creator-ops-reviews.csv",
        [
            "id",
            "content_id",
            "content_title",
            "goal",
            "expected_outcome",
            "what_worked",
            "what_didnt_work",
            "learnings",
            "next_action",
            "created_at",
            "updated_at",
        ],
        [
            [
                row.Review.id,
                row.Review.content_id,
                row.content_title,
                row.Review.goal,
                row.Review.expected_outcome,
                row.Review.what_worked,
                row.Review.what_didnt_work,
                row.Review.learnings,
                row.Review.next_action,
                row.Review.created_at,
                row.Review.updated_at,
            ]
            for row in rows
        ],
    )
