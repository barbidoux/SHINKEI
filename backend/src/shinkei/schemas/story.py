"""Story Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from shinkei.security.validators import PlainText, SanitizedHTML


class StoryBase(BaseModel):
    """Base story schema with common fields."""
    title: PlainText(255) = Field(..., min_length=1)
    synopsis: Optional[SanitizedHTML(10000)] = None
    theme: Optional[PlainText(255)] = Field(None)
    status: str = Field(default="draft", pattern="^(draft|active|completed|archived)$")
    mode: str = Field(default="manual", pattern="^(autonomous|collaborative|manual)$")
    pov_type: str = Field(default="third", pattern="^(first|third|omniscient)$")
    tags: list[str] = Field(default_factory=list, max_length=20, description="Story tags for categorization")


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
    mode: Optional[str] = Field(None, pattern="^(autonomous|collaborative|manual)$")
    pov_type: Optional[str] = Field(None, pattern="^(first|third|omniscient)$")
    tags: Optional[list[str]] = Field(None, max_length=20, description="Story tags for categorization")


class StoryResponse(StoryBase):
    """Schema for story responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    world_id: str
    archived_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer('status', 'mode', 'pov_type')
    def serialize_enums(self, value):
        """Convert enum values to lowercase strings."""
        if hasattr(value, 'value'):
            return value.value.lower()
        return str(value).lower() if value else value


class StoryListResponse(BaseModel):
    """Schema for paginated story list."""
    stories: list[StoryResponse]
    total: int
    page: int
    page_size: int


class StoryStatistics(BaseModel):
    """Statistics about a story."""
    story_id: str
    beat_count: int
    word_count: int
    character_count: int
    ai_generated_count: int
    user_generated_count: int
    collaborative_count: int
    latest_beat_date: Optional[datetime] = None
    world_event_links: int
    beat_type_distribution: dict[str, int] = Field(default_factory=dict)
    estimated_reading_minutes: int
