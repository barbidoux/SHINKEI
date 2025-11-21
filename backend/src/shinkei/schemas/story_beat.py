"""StoryBeat Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from shinkei.security.validators import SanitizedHTML
from shinkei.schemas.story import StoryResponse


class StoryBeatBase(BaseModel):
    """Base story beat schema with common fields."""
    order_index: int = 0
    content: SanitizedHTML(50000) = Field(..., min_length=1)
    type: str = Field(default="scene", pattern="^(scene|summary|note)$")
    world_event_id: Optional[str] = None
    generated_by: str = Field(default="user", pattern="^(ai|user|collaborative)$")
    summary: Optional[str] = None
    local_time_label: Optional[str] = None
    generation_reasoning: Optional[str] = None


class StoryBeatCreate(StoryBeatBase):
    """Schema for creating a new story beat."""
    pass


class StoryBeatUpdate(BaseModel):
    """Schema for updating a story beat."""
    model_config = ConfigDict(extra='forbid')

    order_index: Optional[int] = None
    content: Optional[SanitizedHTML(50000)] = Field(None, min_length=1)
    type: Optional[str] = Field(None, pattern="^(scene|summary|note)$")
    world_event_id: Optional[str] = None
    generated_by: Optional[str] = Field(None, pattern="^(ai|user|collaborative)$")
    summary: Optional[str] = None
    local_time_label: Optional[str] = None
    generation_reasoning: Optional[str] = None


class StoryBeatReasoningUpdate(BaseModel):
    """Schema for updating only the AI reasoning/thoughts for a beat."""
    model_config = ConfigDict(extra='forbid')

    generation_reasoning: Optional[str] = Field(
        None,
        description="AI reasoning/thoughts behind beat generation. Set to null to clear."
    )


class StoryBeatResponse(StoryBeatBase):
    """Schema for story beat responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    story_id: str
    created_at: datetime
    updated_at: datetime

    @field_serializer('type', 'generated_by')
    def serialize_enums(self, value):
        """Convert enum values to lowercase strings."""
        if hasattr(value, 'value'):
            return value.value.lower()
        return str(value).lower() if value else value


class StoryBeatListResponse(BaseModel):
    """Schema for paginated story beat list."""
    beats: list[StoryBeatResponse]
    total: int
    page: int
    page_size: int


class StoryBeatReorderRequest(BaseModel):
    """Schema for reordering story beats."""
    model_config = ConfigDict(extra='forbid')

    beat_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Ordered list of beat IDs in desired sequence"
    )


class BeatWithStoryResponse(BaseModel):
    """Schema for beat with associated story information."""
    model_config = ConfigDict(from_attributes=True)

    # Beat fields
    id: str
    story_id: str
    order_index: int
    content: str
    type: str
    world_event_id: Optional[str] = None
    generated_by: str
    summary: Optional[str] = None
    local_time_label: Optional[str] = None
    generation_reasoning: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Story information
    story: StoryResponse

    @field_serializer('type', 'generated_by')
    def serialize_enums(self, value):
        """Convert enum values to lowercase strings."""
        if hasattr(value, 'value'):
            return value.value.lower()
        return str(value).lower() if value else value
