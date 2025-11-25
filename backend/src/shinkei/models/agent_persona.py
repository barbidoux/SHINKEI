"""Agent Persona model definition for Story Pilot AI Chat Assistant."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid

if TYPE_CHECKING:
    from shinkei.models.world import World
    from shinkei.models.conversation import Conversation


class AgentPersona(Base):
    """
    Agent Persona model representing a customizable AI personality.

    Built-in personas provide default options, while users can create custom
    personas for their worlds.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world this persona belongs to
        name: Display name for the persona
        description: Brief description of the persona's focus/personality
        system_prompt: System prompt defining the persona's behavior
        traits: JSON containing personality traits (strictness, focus_areas, etc.)
        generation_defaults: JSON containing default generation params (temperature, etc.)
        is_builtin: Whether this is a built-in system persona
        is_active: Whether this persona is available for use
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "agent_personas"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Persona UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this persona belongs to"
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Display name for the persona"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Brief description of the persona's focus/personality"
    )

    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="System prompt defining the persona's behavior"
    )

    traits: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Personality traits: strictness, focus_areas, communication_style"
    )

    generation_defaults: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        comment="Default generation parameters: temperature, etc."
    )

    is_builtin: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this is a built-in system persona"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Whether this persona is available for use"
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
    world: Mapped["World"] = relationship("World", back_populates="agent_personas")
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation",
        back_populates="persona",
        foreign_keys="Conversation.persona_id"
    )

    def __repr__(self) -> str:
        return f"<AgentPersona(id={self.id}, name={self.name}, world_id={self.world_id})>"
