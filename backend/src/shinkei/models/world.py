"""World model definition."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid
import enum


class ChronologyMode(str, enum.Enum):
    """Chronology mode enumeration."""
    LINEAR = "linear"
    FRAGMENTED = "fragmented"
    TIMELESS = "timeless"


class World(Base):
    """
    World model representing a narrative universe.
    
    Attributes:
        id: Unique identifier
        user_id: Foreign key to user who created the world
        name: World name
        description: General pitch/summary
        tone: Narrative tone (e.g., "calm, introspective, cold")
        backdrop: World bible, overarching lore
        laws: JSON object containing world rules (physics, metaphysics, social, forbidden)
        chronology_mode: How time flows in this world
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "worlds"
    
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="World UUID"
    )
    
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="World name"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="General pitch/summary"
    )
    
    tone: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Narrative tone"
    )
    
    backdrop: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="World bible, overarching lore"
    )
    
    laws: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="World rules (physics, metaphysics, social, forbidden)"
    )
    
    chronology_mode: Mapped[ChronologyMode] = mapped_column(
        SQLEnum(ChronologyMode),
        nullable=False,
        default=ChronologyMode.LINEAR,
        comment="How time flows in this world"
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
    user: Mapped["User"] = relationship("User", back_populates="worlds")
    world_events: Mapped[list["WorldEvent"]] = relationship(back_populates="world", cascade="all, delete-orphan")
    stories: Mapped[list["Story"]] = relationship("Story", back_populates="world", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship("Conversation", back_populates="world", cascade="all, delete-orphan")

    # Entity relationships (Phase 6)
    characters: Mapped[list["Character"]] = relationship("Character", back_populates="world", cascade="all, delete-orphan")
    locations: Mapped[list["Location"]] = relationship("Location", back_populates="world", cascade="all, delete-orphan")
    character_relationships: Mapped[list["CharacterRelationship"]] = relationship("CharacterRelationship", back_populates="world", cascade="all, delete-orphan")

    # Story Pilot relationships
    agent_personas: Mapped[list["AgentPersona"]] = relationship("AgentPersona", back_populates="world", cascade="all, delete-orphan")
    coherence_settings: Mapped[Optional["WorldCoherenceSettings"]] = relationship("WorldCoherenceSettings", back_populates="world", uselist=False, cascade="all, delete-orphan")
    graph_nodes: Mapped[list["WorldGraphNode"]] = relationship("WorldGraphNode", back_populates="world", cascade="all, delete-orphan")
    graph_edges: Mapped[list["WorldGraphEdge"]] = relationship("WorldGraphEdge", back_populates="world", cascade="all, delete-orphan")
    graph_sync_status: Mapped[Optional["WorldGraphSyncStatus"]] = relationship("WorldGraphSyncStatus", back_populates="world", uselist=False, cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<World(id={self.id}, name={self.name}, user_id={self.user_id})>"
