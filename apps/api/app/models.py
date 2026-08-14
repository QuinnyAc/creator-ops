from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin

topic_tags = Table(
    "topic_tags",
    Base.metadata,
    Column("topic_id", ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

content_tags = Table(
    "content_tags",
    Base.metadata,
    Column("content_id", ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Shanghai", nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)


class Inspiration(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inspirations"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(120))
    source_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="inbox", index=True, nullable=False)
    archived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdeaMemo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "idea_memos"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)


class ContentPillar(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "content_pillars"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_content_pillars_user_name"),)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class Tag(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tags_user_name"),)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class Topic(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "topics"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    inspiration_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("inspirations.id", ondelete="SET NULL"), index=True
    )
    pillar_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_pillars.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    core_idea: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)
    user_problem: Mapped[str | None] = mapped_column(Text)
    angle: Mapped[str | None] = mapped_column(Text)
    goal: Mapped[str | None] = mapped_column(String(48))
    status: Mapped[str] = mapped_column(String(32), default="evaluating", index=True, nullable=False)
    planned_platforms: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)


class TopicScore(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "topic_scores"
    __table_args__ = (
        CheckConstraint("pain_point BETWEEN 1 AND 5", name="pain_point_range"),
        CheckConstraint("search_demand BETWEEN 1 AND 5", name="search_demand_range"),
        CheckConstraint("trend_heat BETWEEN 1 AND 5", name="trend_heat_range"),
        CheckConstraint("differentiation BETWEEN 1 AND 5", name="differentiation_range"),
        CheckConstraint("commercial_value BETWEEN 1 AND 5", name="commercial_value_range"),
        CheckConstraint("production_effort BETWEEN 1 AND 5", name="production_effort_range"),
    )

    topic_id: Mapped[UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    pain_point: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    search_demand: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    trend_heat: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    differentiation: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    commercial_value: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    production_effort: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    opportunity_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)


class Content(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "contents"

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("topics.id", ondelete="SET NULL"), index=True
    )
    pillar_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("content_pillars.id", ondelete="SET NULL"), index=True
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content_type: Mapped[str] = mapped_column(String(48), default="video", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="research", index=True, nullable=False)
    research_notes: Mapped[str | None] = mapped_column(Text)
    outline: Mapped[str | None] = mapped_column(Text)
    script: Mapped[str | None] = mapped_column(Text)
    copywriting: Mapped[str | None] = mapped_column(Text)
    cta: Mapped[str | None] = mapped_column(Text)
    planned_publish_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Platform(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platforms"

    slug: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)


class PlatformAccount(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "platform_accounts"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "platform_id",
            "handle",
            name="uq_platform_accounts_user_platform_handle",
        ),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    platform_id: Mapped[UUID] = mapped_column(
        ForeignKey("platforms.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    handle: Mapped[str | None] = mapped_column(String(160))


class Publication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "publications"

    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    platform_account_id: Mapped[UUID] = mapped_column(
        ForeignKey("platform_accounts.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    title: Mapped[str | None] = mapped_column(String(240))
    copywriting: Mapped[str | None] = mapped_column(Text)
    cover_url: Mapped[str | None] = mapped_column(Text)
    platform_tags: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", index=True, nullable=False)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    url: Mapped[str | None] = mapped_column(Text)


class MetricSnapshot(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "publication_id",
            "captured_at",
            name="uq_metric_snapshots_publication_captured_at",
        ),
    )

    publication_id: Mapped[UUID] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), index=True, nullable=False
    )
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, nullable=False
    )
    views: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    likes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    comments: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    favorites: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    shares: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    followers_gained: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    extra_metrics: Mapped[dict[str, int | float | str]] = mapped_column(
        JSONB, default=dict, nullable=False
    )


class Review(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reviews"

    content_id: Mapped[UUID] = mapped_column(
        ForeignKey("contents.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    goal: Mapped[str | None] = mapped_column(Text)
    expected_outcome: Mapped[str | None] = mapped_column(Text)
    what_worked: Mapped[str | None] = mapped_column(Text)
    what_didnt_work: Mapped[str | None] = mapped_column(Text)
    learnings: Mapped[str | None] = mapped_column(Text)
    next_action: Mapped[str | None] = mapped_column(Text)
