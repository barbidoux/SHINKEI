"""CharacterRelationship model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, func, Enum as SQLEnum, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum


class RelationshipStrength(str, enum.Enum):
    """Strength of relationship between characters."""
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class CharacterRelationship(Base):
    """
    CharacterRelationship model representing connections between characters.
    Defines the nature and strength of relationships within the world.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        character_a_id: First character in the relationship
        character_b_id: Second character in the relationship
        relationship_type: Type of relationship (e.g., friend, enemy, family, ally)
        description: Detailed description of the relationship
        strength: Relationship strength (strong, moderate, weak)
        first_established_beat_id: Story beat where relationship was first established
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "character_relationships"
    __table_args__ = (
        CheckConstraint("character_a_id != character_b_id", name="ck_no_self_relationship"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Relationship UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this relationship belongs to"
    )

    character_a_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="First character in the relationship"
    )

    character_b_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("characters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Second character in the relationship"
    )

    relationship_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Type of relationship (e.g., friend, enemy, family, ally)"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of the relationship"
    )

    strength: Mapped[RelationshipStrength] = mapped_column(
        SQLEnum(RelationshipStrength),
        nullable=False,
        default=RelationshipStrength.MODERATE,
        index=True,
        comment="Relationship strength (strong/moderate/weak)"
    )

    first_established_beat_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("story_beats.id", ondelete="SET NULL"),
        nullable=True,
        comment="Story beat where relationship was first established"
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
    world: Mapped["World"] = relationship("World", back_populates="character_relationships")
    character_a: Mapped["Character"] = relationship(
        "Character",
        foreign_keys=[character_a_id],
        back_populates="relationships_as_a"
    )
    character_b: Mapped["Character"] = relationship(
        "Character",
        foreign_keys=[character_b_id],
        back_populates="relationships_as_b"
    )
    first_established_beat: Mapped[Optional["StoryBeat"]] = relationship(
        "StoryBeat",
        foreign_keys=[first_established_beat_id],
        back_populates="established_relationships"
    )

    def __repr__(self) -> str:
        return f"<CharacterRelationship(id={self.id}, type={self.relationship_type}, strength={self.strength})>"
