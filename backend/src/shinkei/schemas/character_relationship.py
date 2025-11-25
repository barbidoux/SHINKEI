"""CharacterRelationship Pydantic schemas for API validation."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
from shinkei.security.validators import PlainText, SanitizedHTML
from shinkei.schemas.character import CharacterResponse


class CharacterRelationshipBase(BaseModel):
    """Base character relationship schema with common fields."""
    character_a_id: str
    character_b_id: str
    relationship_type: PlainText(100) = Field(..., min_length=1)
    description: Optional[SanitizedHTML(5000)] = None
    strength: str = Field(default="moderate", pattern="^(strong|moderate|weak)$")
    first_established_beat_id: Optional[str] = None

    @field_validator('character_b_id')
    @classmethod
    def validate_no_self_relationship(cls, v: str, info) -> str:
        """Validate that characters are not the same."""
        if 'character_a_id' in info.data and v == info.data['character_a_id']:
            raise ValueError("A character cannot have a relationship with themselves")
        return v


class CharacterRelationshipCreate(CharacterRelationshipBase):
    """Schema for creating a new character relationship."""
    pass


class CharacterRelationshipUpdate(BaseModel):
    """Schema for updating a character relationship."""
    model_config = ConfigDict(extra='forbid')

    relationship_type: Optional[PlainText(100)] = Field(None, min_length=1)
    description: Optional[SanitizedHTML(5000)] = None
    strength: Optional[str] = Field(None, pattern="^(strong|moderate|weak)$")
    first_established_beat_id: Optional[str] = None


class CharacterRelationshipResponse(CharacterRelationshipBase):
    """Schema for character relationship responses."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    world_id: str
    created_at: datetime
    updated_at: datetime


class CharacterRelationshipListResponse(BaseModel):
    """Schema for paginated character relationship list."""
    relationships: list[CharacterRelationshipResponse]
    total: int
    page: int
    page_size: int


class CharacterWithRelationshipsResponse(BaseModel):
    """Schema for character with all their relationships."""
    character: CharacterResponse
    relationships: list[CharacterRelationshipResponse]
    total_relationships: int


class RelationshipNetworkNode(BaseModel):
    """Schema for character in relationship network graph."""
    character_id: str
    character_name: str
    importance: str


class RelationshipNetworkEdge(BaseModel):
    """Schema for relationship edge in network graph."""
    relationship_id: str
    from_character_id: str
    to_character_id: str
    relationship_type: str
    strength: str


class RelationshipNetworkResponse(BaseModel):
    """Schema for relationship network graph data."""
    world_id: str
    nodes: list[RelationshipNetworkNode]
    edges: list[RelationshipNetworkEdge]
    total_characters: int
    total_relationships: int
