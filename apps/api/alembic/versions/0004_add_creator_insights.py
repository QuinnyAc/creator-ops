"""add creator insights playbook table

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-14
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source_review_id", sa.Uuid(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=48), nullable=False, server_default="learning"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_review_id"], ["reviews.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_review_id", name="uq_insights_source_review"),
    )
    op.create_index(op.f("ix_insights_user_id"), "insights", ["user_id"], unique=False)
    op.create_index(op.f("ix_insights_status"), "insights", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_insights_status"), table_name="insights")
    op.drop_index(op.f("ix_insights_user_id"), table_name="insights")
    op.drop_table("insights")
