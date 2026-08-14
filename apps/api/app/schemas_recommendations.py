from uuid import UUID

from pydantic import BaseModel


class TopicRecommendation(BaseModel):
    topic_id: UUID
    title: str
    status: str
    pillar_id: UUID | None
    pillar_name: str | None
    base_priority_score: float
    evidence_adjustment: float
    recommended_score: float
    evidence_publications: int
    pillar_avg_views: float | None
    account_avg_views: float | None
    pillar_favorite_rate: float | None
    account_favorite_rate: float | None
    trend_signal: str | None
    reasons: list[str]
