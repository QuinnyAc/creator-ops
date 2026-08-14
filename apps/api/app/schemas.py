from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


InspirationStatus = Literal["inbox", "converted", "archived"]
TopicStatus = Literal[
    "evaluating",
    "approved",
    "scheduled",
    "in_production",
    "completed",
    "rejected",
    "archived",
]
ContentStatus = Literal[
    "research",
    "outline",
    "script",
    "shooting",
    "editing",
    "ready",
    "published",
    "review",
]
PublicationStatus = Literal["draft", "scheduled", "published", "failed", "archived"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ContentPillarCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class ContentPillarUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None


class ContentPillarRead(ORMModel):
    id: UUID
    user_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


class TagRead(ORMModel):
    id: UUID
    user_id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class InspirationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    note: str | None = None
    source: str | None = Field(default=None, max_length=120)
    source_url: str | None = None


class InspirationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    note: str | None = None
    source: str | None = Field(default=None, max_length=120)
    source_url: str | None = None
    status: InspirationStatus | None = None


class InspirationRead(ORMModel):
    id: UUID
    user_id: UUID
    title: str
    note: str | None
    source: str | None
    source_url: str | None
    status: str
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TopicCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    inspiration_id: UUID | None = None
    pillar_id: UUID | None = None
    core_idea: str | None = None
    target_audience: str | None = None
    user_problem: str | None = None
    angle: str | None = None
    goal: str | None = Field(default=None, max_length=48)
    status: TopicStatus = "evaluating"
    planned_platforms: list[str] = Field(default_factory=list)


class TopicUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    pillar_id: UUID | None = None
    core_idea: str | None = None
    target_audience: str | None = None
    user_problem: str | None = None
    angle: str | None = None
    goal: str | None = Field(default=None, max_length=48)
    status: TopicStatus | None = None
    planned_platforms: list[str] | None = None


class TopicRead(ORMModel):
    id: UUID
    user_id: UUID
    inspiration_id: UUID | None
    pillar_id: UUID | None
    title: str
    core_idea: str | None
    target_audience: str | None
    user_problem: str | None
    angle: str | None
    goal: str | None
    status: str
    planned_platforms: list[str]
    created_at: datetime
    updated_at: datetime


class TopicScoreInput(BaseModel):
    pain_point: int = Field(ge=1, le=5)
    search_demand: int = Field(ge=1, le=5)
    trend_heat: int = Field(ge=1, le=5)
    differentiation: int = Field(ge=1, le=5)
    commercial_value: int = Field(ge=1, le=5)
    production_effort: int = Field(ge=1, le=5)


class TopicScoreRead(ORMModel):
    id: UUID
    topic_id: UUID
    pain_point: int
    search_demand: int
    trend_heat: int
    differentiation: int
    commercial_value: int
    production_effort: int
    opportunity_score: Decimal
    priority_score: Decimal
    created_at: datetime
    updated_at: datetime


class TopicListItem(TopicRead):
    opportunity_score: Decimal | None = None
    priority_score: Decimal | None = None


class InspirationConvertRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    pillar_id: UUID | None = None
    core_idea: str | None = None
    target_audience: str | None = None
    user_problem: str | None = None
    angle: str | None = None
    goal: str | None = Field(default=None, max_length=48)
    planned_platforms: list[str] = Field(default_factory=list)


class ContentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    topic_id: UUID | None = None
    pillar_id: UUID | None = None
    content_type: str = Field(default="video", max_length=48)
    status: ContentStatus = "research"
    research_notes: str | None = None
    outline: str | None = None
    script: str | None = None
    copywriting: str | None = None
    cta: str | None = None
    planned_publish_at: datetime | None = None


class ContentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    topic_id: UUID | None = None
    pillar_id: UUID | None = None
    content_type: str | None = Field(default=None, max_length=48)
    status: ContentStatus | None = None
    research_notes: str | None = None
    outline: str | None = None
    script: str | None = None
    copywriting: str | None = None
    cta: str | None = None
    planned_publish_at: datetime | None = None


class ContentRead(ORMModel):
    id: UUID
    user_id: UUID
    topic_id: UUID | None
    pillar_id: UUID | None
    title: str
    content_type: str
    status: str
    research_notes: str | None
    outline: str | None
    script: str | None
    copywriting: str | None
    cta: str | None
    planned_publish_at: datetime | None
    created_at: datetime
    updated_at: datetime


class PlatformRead(ORMModel):
    id: UUID
    slug: str
    name: str


class PlatformAccountCreate(BaseModel):
    platform_id: UUID
    name: str = Field(min_length=1, max_length=120)
    handle: str | None = Field(default=None, max_length=160)


class PlatformAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    handle: str | None = Field(default=None, max_length=160)


class PlatformAccountRead(ORMModel):
    id: UUID
    user_id: UUID
    platform_id: UUID
    name: str
    handle: str | None
    created_at: datetime
    updated_at: datetime


class PublicationCreate(BaseModel):
    content_id: UUID
    platform_account_id: UUID
    title: str | None = Field(default=None, max_length=240)
    copywriting: str | None = None
    cover_url: str | None = None
    platform_tags: list[str] = Field(default_factory=list)
    status: PublicationStatus = "draft"
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    url: str | None = None


class PublicationUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    copywriting: str | None = None
    cover_url: str | None = None
    platform_tags: list[str] | None = None
    status: PublicationStatus | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    url: str | None = None


class PublicationRead(ORMModel):
    id: UUID
    content_id: UUID
    platform_account_id: UUID
    title: str | None
    copywriting: str | None
    cover_url: str | None
    platform_tags: list[str]
    status: str
    scheduled_at: datetime | None
    published_at: datetime | None
    url: str | None
    created_at: datetime
    updated_at: datetime


class MetricSnapshotCreate(BaseModel):
    captured_at: datetime
    views: int = Field(default=0, ge=0)
    likes: int = Field(default=0, ge=0)
    comments: int = Field(default=0, ge=0)
    favorites: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    followers_gained: int = 0
    extra_metrics: dict[str, int | float | str] = Field(default_factory=dict)


class MetricSnapshotRead(ORMModel):
    id: UUID
    publication_id: UUID
    captured_at: datetime
    views: int
    likes: int
    comments: int
    favorites: int
    shares: int
    followers_gained: int
    extra_metrics: dict[str, int | float | str]


class ReviewUpsert(BaseModel):
    goal: str | None = None
    expected_outcome: str | None = None
    what_worked: str | None = None
    what_didnt_work: str | None = None
    learnings: str | None = None
    next_action: str | None = None


class ReviewRead(ORMModel):
    id: UUID
    content_id: UUID
    goal: str | None
    expected_outcome: str | None
    what_worked: str | None
    what_didnt_work: str | None
    learnings: str | None
    next_action: str | None
    created_at: datetime
    updated_at: datetime


class DashboardSummary(BaseModel):
    inspirations_inbox: int
    topics_approved: int
    contents_in_progress: int
    publications_scheduled: int
    contents_to_review: int


class AnalyticsSummary(BaseModel):
    publications: int
    views: int
    likes: int
    comments: int
    favorites: int
    shares: int
    followers_gained: int
    engagement_rate: float


class ApiMessage(BaseModel):
    message: str


class ErrorDetail(BaseModel):
    detail: str | list[dict[str, Any]]
