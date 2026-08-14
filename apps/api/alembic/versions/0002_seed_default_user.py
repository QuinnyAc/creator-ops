"""seed the local MVP creator user

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-13
"""

from collections.abc import Sequence
from uuid import UUID

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEFAULT_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def upgrade() -> None:
    op.bulk_insert(
        sa.table(
            "users",
            sa.column("id", postgresql.UUID(as_uuid=True)),
            sa.column("email", sa.String()),
            sa.column("display_name", sa.String()),
            sa.column("timezone", sa.String()),
        ),
        [
            {
                "id": DEFAULT_USER_ID,
                "email": "creator@localhost",
                "display_name": "Creator",
                "timezone": "Asia/Shanghai",
            }
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM users WHERE id = :user_id").bindparams(
            sa.bindparam(
                "user_id",
                value=DEFAULT_USER_ID,
                type_=postgresql.UUID(as_uuid=True),
            )
        )
    )
