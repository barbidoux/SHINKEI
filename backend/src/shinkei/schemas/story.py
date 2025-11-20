"""Story Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from shinkei.security.validators import PlainText, SanitizedHTML


class StoryBase(BaseModel):
    """Base story schema with common fields."""
    title: PlainText(255) = Field(..., min_length=1)
    synopsis: Optional[SanitizedHTML(10000)] = None
    theme: Optional[PlainText(255)] = Field(None)
    status: str = Field(default="draft", pattern="^(draft|active|completed|archived)$")


class StoryCreate(StoryBase):
    """Schema for creating a new story."""
    pass


class StoryUpdate(BaseModel):
    """Schema for updating a story."""
    model_config = ConfigDict(extra='forbid')

    title: Optional[PlainText(255)] = Field(None, min_length=1)
    synopsis: Optional[SanitizedHTML(10000)] = None
    theme: Optional[PlainText(255)] = Field(None)
    status: Optional[str] = Field(None, pattern="^(draft|active|completed|archived)$")


class StoryResponse(StoryBase):
    """Schema for story responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    world_id: str
    created_at: datetime
    updated_at: datetime


class StoryListResponse(BaseModel):
    """Schema for paginated story list."""
    stories: list[StoryResponse]
    total: int
    page: int
    page_size: int
