from pydantic import BaseModel


class TitlePatternAnalyticsItem(BaseModel):
    pattern: str
    label: str
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
