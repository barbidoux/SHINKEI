"""Story model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum


class StoryStatus(str, enum.Enum):
    """Story status enumeration."""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AuthoringMode(str, enum.Enum):
    """Authoring mode for story generation."""
    AUTONOMOUS = "autonomous"  # AI generates everything
    COLLABORATIVE = "collaborative"  # AI proposes, user edits
    MANUAL = "manual"  # User writes, AI assists


class POVType(str, enum.Enum):
    """Point of view type for narrative."""
    FIRST = "first"  # First person (I, we)
    THIRD = "third"  # Third person (he, she, they)
    OMNISCIENT = "omniscient"  # Third person omniscient


class Story(Base):
    """
    Story model representing a narrative arc within a world.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        title: Story title
        synopsis: Brief summary
        theme: Central theme
        status: Current status (draft, active, completed, archived)
        mode: Authoring mode (autonomous, collaborative, manual)
        pov_type: Point of view type (first, third, omniscient)
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "stories"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Story UUID"
    )
    
    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this story belongs to"
    )
    
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Story title"
    )
    
    synopsis: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Brief summary"
    )
    
    theme: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Central theme"
    )
    
    status: Mapped[StoryStatus] = mapped_column(
        SQLEnum(StoryStatus),
        nullable=False,
        default=StoryStatus.DRAFT,
        comment="Current status"
    )

    mode: Mapped[AuthoringMode] = mapped_column(
        SQLEnum(AuthoringMode),
        nullable=False,
        default=AuthoringMode.MANUAL,
        comment="Authoring mode (autonomous/collaborative/manual)"
    )

    pov_type: Mapped[POVType] = mapped_column(
        SQLEnum(POVType),
        nullable=False,
        default=POVType.THIRD,
        comment="Point of view type for narrative"
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
    world: Mapped["World"] = relationship("World", back_populates="stories")
    story_beats: Mapped[list["StoryBeat"]] = relationship("StoryBeat", back_populates="story", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Story(id={self.id}, world_id={self.world_id}, title={self.title})>"
