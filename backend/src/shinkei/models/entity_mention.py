"""EntityMention model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Float, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum


class EntityType(str, enum.Enum):
    """Type of entity being mentioned."""
    CHARACTER = "character"
    LOCATION = "location"


class MentionType(str, enum.Enum):
    """Type of mention in the text."""
    EXPLICIT = "explicit"  # Direct mention by name
    IMPLICIT = "implicit"  # Implied presence
    REFERENCED = "referenced"  # Referenced but not present


class DetectionSource(str, enum.Enum):
    """Source of entity detection."""
    USER = "user"  # Manually tagged by user
    AI = "ai"  # Auto-detected by AI


class EntityMention(Base):
    """
    EntityMention model linking entities (characters/locations) to story beats.
    Tracks where entities appear in the narrative.

    Attributes:
        id: Unique identifier
        story_beat_id: Foreign key to story beat
        entity_type: Type of entity (character or location)
        entity_id: ID of the referenced entity
        mention_type: How the entity is mentioned (explicit/implicit/referenced)
        confidence: AI detection confidence score (0.0 to 1.0)
        context_snippet: Text snippet where entity was mentioned
        detected_by: Source of detection (user or ai)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "entity_mentions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Entity mention UUID"
    )

    story_beat_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("story_beats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Story beat where entity is mentioned"
    )

    entity_type: Mapped[EntityType] = mapped_column(
        SQLEnum(EntityType),
        nullable=False,
        index=True,
        comment="Type of entity (character or location)"
    )

    entity_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="ID of the referenced entity (character or location)"
    )

    mention_type: Mapped[MentionType] = mapped_column(
        SQLEnum(MentionType),
        nullable=False,
        default=MentionType.EXPLICIT,
        comment="How the entity is mentioned"
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="AI detection confidence score (0.0 to 1.0)"
    )

    context_snippet: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Text snippet where entity was mentioned"
    )

    detected_by: Mapped[DetectionSource] = mapped_column(
        SQLEnum(DetectionSource),
        nullable=False,
        default=DetectionSource.USER,
        index=True,
        comment="Source of detection (user or ai)"
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
    story_beat: Mapped["StoryBeat"] = relationship("StoryBeat", back_populates="entity_mentions")

    # Polymorphic relationships to character or location
    # Note: These use conditional joins based on entity_type
    # These are viewonly relationships, so they don't use back_populates
    character: Mapped[Optional["Character"]] = relationship(
        "Character",
        foreign_keys=[entity_id],
        primaryjoin="and_(EntityMention.entity_id==foreign(Character.id), EntityMention.entity_type=='character')",
        viewonly=True
    )

    location: Mapped[Optional["Location"]] = relationship(
        "Location",
        foreign_keys=[entity_id],
        primaryjoin="and_(EntityMention.entity_id==foreign(Location.id), EntityMention.entity_type=='location')",
        viewonly=True
    )

    def __repr__(self) -> str:
        return f"<EntityMention(id={self.id}, beat_id={self.story_beat_id}, type={self.entity_type}, entity_id={self.entity_id})>"
