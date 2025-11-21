"""WorldEvent Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class WorldEventBase(BaseModel):
    """Base world event schema with common fields."""
    t: float
    label_time: str = Field(..., min_length=1, max_length=255)
    location_id: Optional[str] = None
    type: str = Field(..., min_length=1, max_length=100)
    summary: str = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    caused_by_ids: list[str] = Field(default_factory=list, description="IDs of events that caused this event")


class WorldEventCreate(WorldEventBase):
    """Schema for creating a new world event."""
    pass


class WorldEventUpdate(BaseModel):
    """Schema for updating a world event."""
    model_config = ConfigDict(extra='forbid')

    t: Optional[float] = None
    label_time: Optional[str] = Field(None, min_length=1, max_length=255)
    location_id: Optional[str] = None
    type: Optional[str] = Field(None, min_length=1, max_length=100)
    summary: Optional[str] = Field(None, min_length=1)
    tags: Optional[list[str]] = None
    caused_by_ids: Optional[list[str]] = Field(None, description="IDs of events that caused this event")


class WorldEventResponse(WorldEventBase):
    """Schema for world event responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    world_id: str
    created_at: datetime
    updated_at: datetime


class WorldEventListResponse(BaseModel):
    """Schema for paginated world event list."""
    events: list[WorldEventResponse]
    total: int
    page: int
    page_size: int
