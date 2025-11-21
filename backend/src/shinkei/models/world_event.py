"""WorldEvent model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, Float, ForeignKey, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
from shinkei.database.engine import Base
import uuid


class WorldEvent(Base):
    """
    WorldEvent model representing a canonical event in world's timeline.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        t: Objective timestamp (can be int or float for flexible time systems)
        label_time: Human-readable time label (e.g., "Log 0017", "Day 42")
        location_id: Optional reference to location (for future GraphRAG)
        type: Event type (incident, glitch, meeting, etc.)
        summary: Brief description of the event
        tags: Array of tags for categorization
        caused_by_ids: Array of event IDs that caused this event (dependency graph)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "world_events"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="WorldEvent UUID"
    )
    
    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this event belongs to"
    )
    
    t: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Objective timestamp in world time"
    )
    
    label_time: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable time label"
    )
    
    location_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Location reference (for future GraphRAG)"
    )
    
    type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Event type (incident, glitch, meeting, etc.)"
    )
    
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Brief description of the event"
    )
    
    tags: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="Tags for categorization"
    )

    caused_by_ids: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        nullable=False,
        default=list,
        comment="IDs of events that caused this event (dependency graph)"
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
    world: Mapped["World"] = relationship("World", back_populates="world_events")
    story_beats: Mapped[list["StoryBeat"]] = relationship("StoryBeat", back_populates="world_event")
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('ix_world_events_world_t', 'world_id', 't'),
        Index('ix_world_events_type', 'type'),
    )
    
    def __repr__(self) -> str:
        return f"<WorldEvent(id={self.id}, world_id={self.world_id}, t={self.t}, label_time={self.label_time})>"
