"""EntityMention Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from shinkei.security.validators import SanitizedHTML


class EntityMentionBase(BaseModel):
    """Base entity mention schema with common fields."""
    entity_type: str = Field(..., pattern="^(character|location)$")
    entity_id: str
    mention_type: str = Field(default="explicit", pattern="^(explicit|implicit|referenced)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    context_snippet: Optional[SanitizedHTML(1000)] = None
    detected_by: str = Field(default="user", pattern="^(user|ai)$")

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        """Validate confidence is in valid range."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class EntityMentionCreate(EntityMentionBase):
    """Schema for creating a new entity mention."""
    pass


class EntityMentionUpdate(BaseModel):
    """Schema for updating an entity mention."""
    model_config = ConfigDict(extra='forbid')

    mention_type: Optional[str] = Field(None, pattern="^(explicit|implicit|referenced)$")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    context_snippet: Optional[SanitizedHTML(1000)] = None
    detected_by: Optional[str] = Field(None, pattern="^(user|ai)$")


class EntityMentionResponse(EntityMentionBase):
    """Schema for entity mention responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    story_beat_id: str
    created_at: datetime
    updated_at: datetime


class EntityMentionListResponse(BaseModel):
    """Schema for paginated entity mention list."""
    mentions: list[EntityMentionResponse]
    total: int
    page: int
    page_size: int


class EntityTimelineItem(BaseModel):
    """Schema for entity timeline item."""
    story_beat_id: str
    story_id: str
    story_title: str
    beat_order_index: int
    mention_type: str
    context_snippet: Optional[str] = None
    created_at: datetime


class EntityTimelineResponse(BaseModel):
    """Schema for entity timeline across all stories."""
    entity_id: str
    entity_type: str
    entity_name: str
    mentions: list[EntityTimelineItem]
    total_mentions: int


class BulkEntityMentionCreate(BaseModel):
    """Schema for creating multiple entity mentions at once."""
    mentions: list[EntityMentionCreate] = Field(..., min_length=1, max_length=50)
