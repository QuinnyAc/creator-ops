from uuid import UUID

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Insight(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "insights"
    __table_args__ = (
        UniqueConstraint("source_review_id", name="uq_insights_source_review"),
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_review_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("reviews.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(48), default="learning", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True, nullable=False)
