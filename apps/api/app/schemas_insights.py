from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

InsightStatus = Literal["active", "archived"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class InsightCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    body: str = Field(min_length=1)
    category: str = Field(default="learning", min_length=1, max_length=48)


class InsightUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    body: str | None = Field(default=None, min_length=1)
    category: str | None = Field(default=None, min_length=1, max_length=48)
    status: InsightStatus | None = None


class InsightPromoteRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    category: str = Field(default="content-learning", min_length=1, max_length=48)


class InsightRead(ORMModel):
    id: UUID
    user_id: UUID
    source_review_id: UUID | None
    title: str
    body: str
    category: str
    status: str
    created_at: datetime
    updated_at: datetime
