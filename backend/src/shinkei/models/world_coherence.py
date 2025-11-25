"""World Coherence Settings model definition for Story Pilot AI Chat Assistant."""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid

if TYPE_CHECKING:
    from shinkei.models.world import World


class WorldCoherenceSettings(Base):
    """
    World Coherence Settings model for configuring per-world coherence rules.

    These settings allow users to customize how strictly the AI enforces
    world consistency - useful for non-euclidean, timeless, or paradox-allowed
    narrative worlds.

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world (one-to-one relationship)
        time_consistency: How time flows (strict, flexible, non-linear, irrelevant)
        spatial_consistency: Spatial rules (euclidean, flexible, non-euclidean, irrelevant)
        causality: Cause-effect rules (strict, flexible, paradox-allowed)
        character_knowledge: Character info access (strict, flexible)
        death_permanence: Death rules (permanent, reversible, fluid)
        custom_rules: Array of free-form custom coherence rules
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "world_coherence_settings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Settings UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="World ID (one-to-one relationship)"
    )

    # Physics/Logic coherence
    time_consistency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="strict",
        comment="Time coherence: strict, flexible, non-linear, irrelevant"
    )

    spatial_consistency: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="euclidean",
        comment="Spatial rules: euclidean, flexible, non-euclidean, irrelevant"
    )

    causality: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="strict",
        comment="Cause-effect: strict, flexible, paradox-allowed"
    )

    # Narrative coherence
    character_knowledge: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="strict",
        comment="Character info access: strict, flexible"
    )

    death_permanence: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="permanent",
        comment="Death rules: permanent, reversible, fluid"
    )

    # Custom rules (free-form)
    custom_rules: Mapped[Optional[List[str]]] = mapped_column(
        ARRAY(Text),
        nullable=True,
        comment="Array of custom coherence rules"
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
    world: Mapped["World"] = relationship("World", back_populates="coherence_settings")

    def __repr__(self) -> str:
        return f"<WorldCoherenceSettings(id={self.id}, world_id={self.world_id})>"

    # Valid options for each field (for validation)
    TIME_CONSISTENCY_OPTIONS = ["strict", "flexible", "non-linear", "irrelevant"]
    SPATIAL_CONSISTENCY_OPTIONS = ["euclidean", "flexible", "non-euclidean", "irrelevant"]
    CAUSALITY_OPTIONS = ["strict", "flexible", "paradox-allowed"]
    CHARACTER_KNOWLEDGE_OPTIONS = ["strict", "flexible"]
    DEATH_PERMANENCE_OPTIONS = ["permanent", "reversible", "fluid"]
