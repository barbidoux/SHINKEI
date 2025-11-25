"""Location model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, func, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid


class Location(Base):
    """
    Location model representing a place within a world.
    Supports hierarchical structure (parent-child relationships).

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        name: Location name
        description: Location description
        location_type: Type of location (e.g., city, building, planet, region)
        parent_location_id: Parent location for hierarchical structure
        significance: Narrative significance of the location
        first_appearance_beat_id: Story beat where location first appeared
        coordinates: Flexible JSON coordinates (lat/long, x/y/z, etc.)
        metadata: Flexible JSON metadata
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Location UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this location belongs to"
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Location name"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Location description"
    )

    location_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Type of location (e.g., city, building, planet, region)"
    )

    parent_location_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("locations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Parent location for hierarchical structure"
    )

    significance: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Narrative significance of the location"
    )

    first_appearance_beat_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("story_beats.id", ondelete="SET NULL"),
        nullable=True,
        comment="Story beat where location first appeared"
    )

    coordinates: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        comment="Flexible coordinate storage (lat/long, x/y/z, etc.)"
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
    world: Mapped["World"] = relationship("World", back_populates="locations")
    first_appearance_beat: Mapped[Optional["StoryBeat"]] = relationship(
        "StoryBeat",
        foreign_keys=[first_appearance_beat_id],
        back_populates="first_appearance_locations"
    )
    parent_location: Mapped[Optional["Location"]] = relationship(
        "Location",
        remote_side=[id],
        foreign_keys=[parent_location_id],
        back_populates="child_locations"
    )
    child_locations: Mapped[list["Location"]] = relationship(
        "Location",
        remote_side=[parent_location_id],
        back_populates="parent_location",
        cascade="all, delete-orphan"
    )
    mentions: Mapped[list["EntityMention"]] = relationship(
        "EntityMention",
        foreign_keys="[EntityMention.entity_id]",
        primaryjoin="and_(Location.id==foreign(EntityMention.entity_id), EntityMention.entity_type=='location')",
        cascade="all, delete-orphan",
        overlaps="mentions"
    )

    def __repr__(self) -> str:
        return f"<Location(id={self.id}, world_id={self.world_id}, name={self.name})>"
