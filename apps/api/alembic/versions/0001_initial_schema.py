"""initial creator ops schema

Revision ID: 0001
Revises:
Create Date: 2026-08-13
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)

    op.create_table(
        "users",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "inspirations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("source", sa.String(length=120)),
        sa.Column("source_url", sa.Text()),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_inspirations_user_id", "inspirations", ["user_id"])
    op.create_index("ix_inspirations_status", "inspirations", ["status"])

    op.create_table(
        "content_pillars",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text()),
        *_timestamps(),
        sa.UniqueConstraint(
            "user_id",
            "name",
            name="uq_content_pillars_user_name",
        ),
    )
    op.create_index("ix_content_pillars_user_id", "content_pillars", ["user_id"])

    op.create_table(
        "tags",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=80), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("user_id", "name", name="uq_tags_user_name"),
    )
    op.create_index("ix_tags_user_id", "tags", ["user_id"])

    op.create_table(
        "platforms",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("slug", sa.String(length=48), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("slug", name="uq_platforms_slug"),
        sa.UniqueConstraint("name", name="uq_platforms_name"),
    )

    op.create_table(
        "topics",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "inspiration_id",
            uuid,
            sa.ForeignKey("inspirations.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "pillar_id",
            uuid,
            sa.ForeignKey("content_pillars.id", ondelete="SET NULL"),
        ),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("core_idea", sa.Text()),
        sa.Column("target_audience", sa.Text()),
        sa.Column("user_problem", sa.Text()),
        sa.Column("angle", sa.Text()),
        sa.Column("goal", sa.String(length=48)),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "planned_platforms",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        *_timestamps(),
    )
    op.create_index("ix_topics_user_id", "topics", ["user_id"])
    op.create_index("ix_topics_inspiration_id", "topics", ["inspiration_id"])
    op.create_index("ix_topics_pillar_id", "topics", ["pillar_id"])
    op.create_index("ix_topics_status", "topics", ["status"])

    op.create_table(
        "topic_scores",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "topic_id",
            uuid,
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("pain_point", sa.SmallInteger(), nullable=False),
        sa.Column("search_demand", sa.SmallInteger(), nullable=False),
        sa.Column("trend_heat", sa.SmallInteger(), nullable=False),
        sa.Column("differentiation", sa.SmallInteger(), nullable=False),
        sa.Column("commercial_value", sa.SmallInteger(), nullable=False),
        sa.Column("production_effort", sa.SmallInteger(), nullable=False),
        sa.Column("opportunity_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("priority_score", sa.Numeric(5, 2), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "pain_point BETWEEN 1 AND 5",
            name="ck_topic_scores_pain_point_range",
        ),
        sa.CheckConstraint(
            "search_demand BETWEEN 1 AND 5",
            name="ck_topic_scores_search_demand_range",
        ),
        sa.CheckConstraint(
            "trend_heat BETWEEN 1 AND 5",
            name="ck_topic_scores_trend_heat_range",
        ),
        sa.CheckConstraint(
            "differentiation BETWEEN 1 AND 5",
            name="ck_topic_scores_differentiation_range",
        ),
        sa.CheckConstraint(
            "commercial_value BETWEEN 1 AND 5",
            name="ck_topic_scores_commercial_value_range",
        ),
        sa.CheckConstraint(
            "production_effort BETWEEN 1 AND 5",
            name="ck_topic_scores_production_effort_range",
        ),
        sa.UniqueConstraint("topic_id", name="uq_topic_scores_topic_id"),
    )
    op.create_index("ix_topic_scores_topic_id", "topic_scores", ["topic_id"])

    op.create_table(
        "contents",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "topic_id",
            uuid,
            sa.ForeignKey("topics.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "pillar_id",
            uuid,
            sa.ForeignKey("content_pillars.id", ondelete="SET NULL"),
        ),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("content_type", sa.String(length=48), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("research_notes", sa.Text()),
        sa.Column("outline", sa.Text()),
        sa.Column("script", sa.Text()),
        sa.Column("copywriting", sa.Text()),
        sa.Column("cta", sa.Text()),
        sa.Column("planned_publish_at", sa.DateTime(timezone=True)),
        *_timestamps(),
    )
    op.create_index("ix_contents_user_id", "contents", ["user_id"])
    op.create_index("ix_contents_topic_id", "contents", ["topic_id"])
    op.create_index("ix_contents_pillar_id", "contents", ["pillar_id"])
    op.create_index("ix_contents_status", "contents", ["status"])

    op.create_table(
        "platform_accounts",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "user_id",
            uuid,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "platform_id",
            uuid,
            sa.ForeignKey("platforms.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("handle", sa.String(length=160)),
        *_timestamps(),
        sa.UniqueConstraint(
            "user_id",
            "platform_id",
            "handle",
            name="uq_platform_accounts_user_platform_handle",
        ),
    )
    op.create_index("ix_platform_accounts_user_id", "platform_accounts", ["user_id"])
    op.create_index(
        "ix_platform_accounts_platform_id",
        "platform_accounts",
        ["platform_id"],
    )

    op.create_table(
        "topic_tags",
        sa.Column(
            "topic_id",
            uuid,
            sa.ForeignKey("topics.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            uuid,
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "content_tags",
        sa.Column(
            "content_id",
            uuid,
            sa.ForeignKey("contents.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            uuid,
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "publications",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "content_id",
            uuid,
            sa.ForeignKey("contents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "platform_account_id",
            uuid,
            sa.ForeignKey("platform_accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=240)),
        sa.Column("copywriting", sa.Text()),
        sa.Column("cover_url", sa.Text()),
        sa.Column(
            "platform_tags",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("url", sa.Text()),
        *_timestamps(),
    )
    op.create_index("ix_publications_content_id", "publications", ["content_id"])
    op.create_index(
        "ix_publications_platform_account_id",
        "publications",
        ["platform_account_id"],
    )
    op.create_index("ix_publications_status", "publications", ["status"])
    op.create_index("ix_publications_scheduled_at", "publications", ["scheduled_at"])
    op.create_index("ix_publications_published_at", "publications", ["published_at"])

    op.create_table(
        "metric_snapshots",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "publication_id",
            uuid,
            sa.ForeignKey("publications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("views", sa.BigInteger(), nullable=False),
        sa.Column("likes", sa.BigInteger(), nullable=False),
        sa.Column("comments", sa.BigInteger(), nullable=False),
        sa.Column("favorites", sa.BigInteger(), nullable=False),
        sa.Column("shares", sa.BigInteger(), nullable=False),
        sa.Column("followers_gained", sa.BigInteger(), nullable=False),
        sa.Column(
            "extra_metrics",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "publication_id",
            "captured_at",
            name="uq_metric_snapshots_publication_captured_at",
        ),
    )
    op.create_index(
        "ix_metric_snapshots_publication_id",
        "metric_snapshots",
        ["publication_id"],
    )
    op.create_index(
        "ix_metric_snapshots_captured_at",
        "metric_snapshots",
        ["captured_at"],
    )

    op.create_table(
        "reviews",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "content_id",
            uuid,
            sa.ForeignKey("contents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("goal", sa.Text()),
        sa.Column("expected_outcome", sa.Text()),
        sa.Column("what_worked", sa.Text()),
        sa.Column("what_didnt_work", sa.Text()),
        sa.Column("learnings", sa.Text()),
        sa.Column("next_action", sa.Text()),
        *_timestamps(),
        sa.UniqueConstraint("content_id", name="uq_reviews_content_id"),
    )
    op.create_index("ix_reviews_content_id", "reviews", ["content_id"])

    op.bulk_insert(
        sa.table(
            "platforms",
            sa.column("id", uuid),
            sa.column("slug", sa.String()),
            sa.column("name", sa.String()),
        ),
        [
            {
                "id": "10000000-0000-0000-0000-000000000001",
                "slug": "xiaohongshu",
                "name": "Xiaohongshu",
            },
            {
                "id": "10000000-0000-0000-0000-000000000002",
                "slug": "bilibili",
                "name": "Bilibili",
            },
            {
                "id": "10000000-0000-0000-0000-000000000003",
                "slug": "wechat_official",
                "name": "WeChat Official Accounts",
            },
            {
                "id": "10000000-0000-0000-0000-000000000004",
                "slug": "youtube",
                "name": "YouTube",
            },
        ],
    )


def downgrade() -> None:
    op.drop_table("reviews")
    op.drop_table("metric_snapshots")
    op.drop_table("publications")
    op.drop_table("content_tags")
    op.drop_table("topic_tags")
    op.drop_table("platform_accounts")
    op.drop_table("contents")
    op.drop_table("topic_scores")
    op.drop_table("topics")
    op.drop_table("platforms")
    op.drop_table("tags")
    op.drop_table("content_pillars")
    op.drop_table("inspirations")
    op.drop_table("users")
