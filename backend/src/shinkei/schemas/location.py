"""Location Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from shinkei.security.validators import PlainText, SanitizedHTML


class LocationBase(BaseModel):
    """Base location schema with common fields."""
    name: PlainText(200) = Field(..., min_length=1)
    description: Optional[SanitizedHTML(10000)] = None
    location_type: Optional[PlainText(50)] = None
    parent_location_id: Optional[str] = None
    significance: Optional[SanitizedHTML(5000)] = None
    first_appearance_beat_id: Optional[str] = None
    coordinates: Optional[dict] = None
    custom_metadata: Optional[dict] = None


class LocationCreate(LocationBase):
    """Schema for creating a new location."""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location."""
    model_config = ConfigDict(extra='forbid')

    name: Optional[PlainText(200)] = Field(None, min_length=1)
    description: Optional[SanitizedHTML(10000)] = None
    location_type: Optional[PlainText(50)] = None
    parent_location_id: Optional[str] = None
    significance: Optional[SanitizedHTML(5000)] = None
    first_appearance_beat_id: Optional[str] = None
    coordinates: Optional[dict] = None
    custom_metadata: Optional[dict] = None


class LocationResponse(LocationBase):
    """Schema for location responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    world_id: str
    created_at: datetime
    updated_at: datetime


class LocationListResponse(BaseModel):
    """Schema for paginated location list."""
    locations: list[LocationResponse]
    total: int
    page: int
    page_size: int


class LocationHierarchyResponse(LocationResponse):
    """Schema for location with hierarchical information."""
    parent_location: Optional[LocationResponse] = None
    child_locations: list[LocationResponse] = Field(default_factory=list)


class LocationWithMentionsResponse(LocationResponse):
    """Schema for location with mention count."""
    mention_count: int = 0
