"""StoryBeat model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum


class BeatType(str, enum.Enum):
    """Beat type enumeration."""
    SCENE = "scene"
    SUMMARY = "summary"
    NOTE = "note"


class GeneratedBy(str, enum.Enum):
    """Source of beat generation."""
    AI = "ai"  # Fully AI-generated
    USER = "user"  # Manually written by user
    COLLABORATIVE = "collaborative"  # AI-generated with user edits


class StoryBeat(Base):
    """
    StoryBeat model representing an atomic unit of narrative.

    Attributes:
        id: Unique identifier
        story_id: Foreign key to story
        order_index: Ordering within the story (1, 2, 3...)
        content: The actual text content
        type: Beat type (scene, summary, note)
        world_event_id: Optional link to a canonical world event
        generated_by: Source of generation (ai, user, collaborative)
        summary: Short summary for UI display
        local_time_label: In-world narrative timestamp
        generation_reasoning: AI reasoning/thoughts behind beat generation
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "story_beats"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="StoryBeat UUID"
    )
    
    story_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Story ID this beat belongs to"
    )
    
    order_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Ordering within the story"
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual text content"
    )
    
    type: Mapped[BeatType] = mapped_column(
        SQLEnum(BeatType),
        nullable=False,
        default=BeatType.SCENE,
        comment="Beat type"
    )
    
    world_event_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("world_events.id", ondelete="SET NULL"),
        nullable=True,
        comment="Optional link to a canonical world event"
    )

    generated_by: Mapped[GeneratedBy] = mapped_column(
        SQLEnum(GeneratedBy),
        nullable=False,
        default=GeneratedBy.USER,
        comment="Source of beat generation (ai/user/collaborative)"
    )

    summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Short summary for UI display (auto-generated for AI beats)"
    )

    local_time_label: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="In-world narrative timestamp (e.g., 'Day 3', 'Log 0017')"
    )

    generation_reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI reasoning/thoughts behind beat generation"
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
    story: Mapped["Story"] = relationship("Story", back_populates="story_beats")
    world_event: Mapped[Optional["WorldEvent"]] = relationship("WorldEvent", back_populates="story_beats")
    modifications: Mapped[list["BeatModification"]] = relationship("BeatModification", back_populates="beat", cascade="all, delete-orphan", order_by="desc(BeatModification.created_at)")
    
    def __repr__(self) -> str:
        return f"<StoryBeat(id={self.id}, story_id={self.story_id}, order={self.order_index})>"
