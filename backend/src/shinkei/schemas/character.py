"""Character Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from shinkei.security.validators import PlainText, SanitizedHTML


class CharacterBase(BaseModel):
    """Base character schema with common fields."""
    name: PlainText(200) = Field(..., min_length=1)
    description: Optional[SanitizedHTML(10000)] = None
    aliases: Optional[list[PlainText(100)]] = Field(None, max_length=10)
    role: Optional[PlainText(200)] = None
    importance: str = Field(default="background", pattern="^(major|minor|background)$")
    first_appearance_beat_id: Optional[str] = None
    custom_metadata: Optional[dict] = None


class CharacterCreate(CharacterBase):
    """Schema for creating a new character."""
    pass


class CharacterUpdate(BaseModel):
    """Schema for updating a character."""
    model_config = ConfigDict(extra='forbid')

    name: Optional[PlainText(200)] = Field(None, min_length=1)
    description: Optional[SanitizedHTML(10000)] = None
    aliases: Optional[list[PlainText(100)]] = Field(None, max_length=10)
    role: Optional[PlainText(200)] = None
    importance: Optional[str] = Field(None, pattern="^(major|minor|background)$")
    first_appearance_beat_id: Optional[str] = None
    custom_metadata: Optional[dict] = None


class CharacterResponse(CharacterBase):
    """Schema for character responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    world_id: str
    created_at: datetime
    updated_at: datetime


class CharacterListResponse(BaseModel):
    """Schema for paginated character list."""
    characters: list[CharacterResponse]
    total: int
    page: int
    page_size: int


class CharacterWithMentionsResponse(CharacterResponse):
    """Schema for character with mention count."""
    mention_count: int = 0


class CharacterSearchResponse(BaseModel):
    """Schema for character search results."""
    characters: list[CharacterWithMentionsResponse]
    total: int
