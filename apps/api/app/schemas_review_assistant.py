from pydantic import BaseModel


class ReviewMetricsSummary(BaseModel):
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


class ReviewSuggestion(BaseModel):
    metrics: ReviewMetricsSummary
    baseline: ReviewMetricsSummary
    title_patterns: list[str]
    what_worked: str
    what_didnt_work: str
    learnings: str
    next_action: str
