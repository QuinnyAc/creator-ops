"""focus platform catalog on Xiaohongshu and Bilibili

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-14
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("UPDATE platforms SET name = '小红书' WHERE slug = 'xiaohongshu'")
    op.execute("UPDATE platforms SET name = '哔哩哔哩' WHERE slug = 'bilibili'")

    # Remove retired platforms only when no historical platform account references them.
    # Referenced rows are intentionally preserved for data integrity and are hidden by the API.
    op.execute(
        """
        DELETE FROM platforms AS p
        WHERE p.slug IN ('youtube', 'wechat_official')
          AND NOT EXISTS (
              SELECT 1 FROM platform_accounts AS pa WHERE pa.platform_id = p.id
          )
        """
    )


def downgrade() -> None:
    op.execute("UPDATE platforms SET name = 'Xiaohongshu' WHERE slug = 'xiaohongshu'")
    op.execute("UPDATE platforms SET name = 'Bilibili' WHERE slug = 'bilibili'")
