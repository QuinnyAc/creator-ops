from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas import TagRead, TopicListItem


class TagAssignment(BaseModel):
    tag_ids: list[UUID] = Field(default_factory=list, max_length=50)


class TopicLibraryItem(TopicListItem):
    tags: list[TagRead] = Field(default_factory=list)
