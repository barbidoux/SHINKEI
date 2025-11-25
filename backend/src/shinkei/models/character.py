"""Character model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, func, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum


class EntityImportance(str, enum.Enum):
    """Entity importance level enumeration."""
    MAJOR = "major"  # Primary character
    MINOR = "minor"  # Secondary character
    BACKGROUND = "background"  # Background/mentioned character


class Character(Base):
    """
    Character model representing a person or entity within a world.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        name: Character name
        description: Character description
        aliases: List of alternative names
        role: Character role (e.g., protagonist, antagonist, mentor)
        importance: Importance level (major, minor, background)
        first_appearance_beat_id: Story beat where character first appeared
        metadata: Flexible JSON metadata
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Character UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this character belongs to"
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Character name"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Character description"
    )

    aliases: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(100)),
        nullable=True,
        comment="Alternative names or aliases"
    )

    role: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Character role (e.g., protagonist, antagonist, mentor)"
    )

    importance: Mapped[EntityImportance] = mapped_column(
        SQLEnum(EntityImportance),
        nullable=False,
        default=EntityImportance.BACKGROUND,
        comment="Importance level (major/minor/background)"
    )

    first_appearance_beat_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("story_beats.id", ondelete="SET NULL"),
        nullable=True,
        comment="Story beat where character first appeared"
    )

    custom_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Database column name
        JSON,
        nullable=True,
        comment="Flexible JSON metadata for custom attributes"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp of creation"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp of last update"
    )

    # Relationships
    world: Mapped["World"] = relationship("World", back_populates="characters")
    first_appearance_beat: Mapped[Optional["StoryBeat"]] = relationship(
        "StoryBeat",
        foreign_keys=[first_appearance_beat_id],
        back_populates="first_appearance_characters"
    )
    mentions: Mapped[list["EntityMention"]] = relationship(
        "EntityMention",
        foreign_keys="[EntityMention.entity_id]",
        primaryjoin="and_(Character.id==foreign(EntityMention.entity_id), EntityMention.entity_type=='character')",
        cascade="all, delete-orphan"
    )
    relationships_as_a: Mapped[list["CharacterRelationship"]] = relationship(
        "CharacterRelationship",
        foreign_keys="[CharacterRelationship.character_a_id]",
        back_populates="character_a",
        cascade="all, delete-orphan"
    )
    relationships_as_b: Mapped[list["CharacterRelationship"]] = relationship(
        "CharacterRelationship",
        foreign_keys="[CharacterRelationship.character_b_id]",
        back_populates="character_b",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Character(id={self.id}, world_id={self.world_id}, name={self.name})>"
