"""BeatModification model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid


class BeatModification(Base):
    """
    BeatModification model representing a modification history entry for a beat.

    Tracks the last 10 modifications per beat, including original/modified content,
    AI reasoning, and whether the modification was applied.

    Attributes:
        id: Unique identifier
        beat_id: Foreign key to StoryBeat
        original_content: Original beat content before modification
        modified_content: AI-suggested modified content
        original_summary: Original beat summary
        modified_summary: AI-suggested modified summary
        original_time_label: Original time label
        modified_time_label: AI-suggested modified time label
        original_world_event_id: Original world event link
        modified_world_event_id: AI-suggested world event link
        modification_instructions: User's instructions for modification
        reasoning: AI's reasoning for the changes made
        unified_diff: Unified diff showing changes
        applied: Whether this modification was accepted and applied
        created_at: Timestamp of modification creation
    """
    __tablename__ = "beat_modifications"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Modification UUID"
    )

    beat_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("story_beats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Beat being modified"
    )

    original_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Original beat content"
    )

    modified_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Modified beat content"
    )

    original_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Original beat summary"
    )

    modified_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Modified beat summary"
    )

    original_time_label: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Original time label"
    )

    modified_time_label: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Modified time label"
    )

    original_world_event_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Original world event link"
    )

    modified_world_event_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        nullable=True,
        comment="Modified world event link"
    )

    modification_instructions: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="User instructions for modification"
    )

    reasoning: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI reasoning for changes"
    )

    unified_diff: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Unified diff of changes"
    )

    applied: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="false",
        index=True,
        comment="Whether modification was applied"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
        comment="Timestamp of modification"
    )

    # Relationships
    beat: Mapped["StoryBeat"] = relationship("StoryBeat", back_populates="modifications")

    def __repr__(self) -> str:
        return f"<BeatModification(id={self.id}, beat_id={self.beat_id}, applied={self.applied})>"
