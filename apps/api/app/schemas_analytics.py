from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class PillarAnalyticsItem(BaseModel):
    pillar_id: UUID
    pillar_name: str
    publications: int
    views: int
    likes: int
    comments: int
    favorites: int
    shares: int
    followers_gained: int
    avg_views: float
    engagement_rate: float
    favorite_rate: float
    follower_conversion_rate: float


class PillarTrendItem(BaseModel):
    pillar_id: UUID
    pillar_name: str
    recent_publications: int
    previous_publications: int
    recent_avg_views: float
    previous_avg_views: float
    view_change_percent: float | None
    recent_favorite_rate: float
    previous_favorite_rate: float
    signal: Literal["rising", "stable", "falling", "new", "insufficient"]


class PlatformAnalyticsItem(BaseModel):
    platform_id: UUID
    platform_slug: str
    platform_name: str
    publications: int
    views: int
    likes: int
    comments: int
    favorites: int
    shares: int
    followers_gained: int
    avg_views: float
    engagement_rate: float
    favorite_rate: float
    follower_conversion_rate: float


class PerformanceMilestone(BaseModel):
    label: str
    target_hours: int
    target_at: datetime | None
    captured_at: datetime | None
    views: int | None
    likes: int | None
    comments: int | None
    favorites: int | None
    shares: int | None
    followers_gained: int | None
