"""World Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from shinkei.security.validators import PlainText, SanitizedHTML


class WorldLaws(BaseModel):
    """World laws schema with sanitized fields."""
    physics: Optional[SanitizedHTML(10000)] = None
    metaphysics: Optional[SanitizedHTML(10000)] = None
    social: Optional[SanitizedHTML(10000)] = None
    forbidden: Optional[SanitizedHTML(10000)] = None


class WorldBase(BaseModel):
    """Base world schema with common fields."""
    name: PlainText(255) = Field(..., min_length=1)
    description: Optional[SanitizedHTML(5000)] = None
    tone: Optional[PlainText(500)] = Field(None)
    backdrop: Optional[SanitizedHTML(20000)] = None
    laws: WorldLaws = Field(default_factory=WorldLaws)
    chronology_mode: str = Field(default="linear", pattern="^(linear|fragmented|timeless)$")


class WorldCreate(WorldBase):
    """Schema for creating a new world."""
    pass


class WorldUpdate(BaseModel):
    """Schema for updating a world."""
    model_config = ConfigDict(extra='forbid')

    name: Optional[PlainText(255)] = Field(None, min_length=1)
    description: Optional[SanitizedHTML(5000)] = None
    tone: Optional[PlainText(500)] = Field(None)
    backdrop: Optional[SanitizedHTML(20000)] = None
    laws: Optional[WorldLaws] = None
    chronology_mode: Optional[str] = Field(None, pattern="^(linear|fragmented|timeless)$")


class WorldResponse(WorldBase):
    """Schema for world responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class WorldListResponse(BaseModel):
    """Schema for paginated world list."""
    worlds: list[WorldResponse]
    total: int
    page: int
    page_size: int
