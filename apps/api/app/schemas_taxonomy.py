from uuid import UUID

from pydantic import BaseModel, Field


class TagAssignment(BaseModel):
    tag_ids: list[UUID] = Field(default_factory=list, max_length=50)
