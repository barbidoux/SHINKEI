"""GraphRAG models for Story Pilot AI Chat Assistant.

These models implement the knowledge graph for semantic search and
entity relationship traversal within a world's content.
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, Text, JSON, DateTime, ForeignKey, func, Float, Integer, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shinkei.database.engine import Base
import uuid

if TYPE_CHECKING:
    from shinkei.models.world import World


class WorldGraphNode(Base):
    """
    Node in the world knowledge graph representing an entity.

    Stores embeddings and metadata for semantic search across all
    world entities (characters, locations, events, stories, beats).

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        entity_type: Type of entity (character, location, event, story, beat)
        entity_id: ID of the referenced entity
        content_hash: Hash of source content for change detection
        embedding: Vector embedding as JSON array
        semantic_summary: AI-generated summary of entity for context
        importance_score: PageRank-like score for entity importance
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """
    __tablename__ = "world_graph_nodes"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Node UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID this node belongs to"
    )

    # Entity reference (polymorphic)
    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Entity type: character, location, event, story, beat"
    )

    entity_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
        comment="Referenced entity ID"
    )

    # Semantic data
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="SHA-256 hash of source content for change detection"
    )

    embedding: Mapped[Optional[List[float]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Vector embedding as JSON array"
    )

    semantic_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="AI-generated summary of entity"
    )

    # Graph metrics
    importance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        index=True,
        comment="PageRank-like importance score"
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
    world: Mapped["World"] = relationship("World", back_populates="graph_nodes")
    outgoing_edges: Mapped[List["WorldGraphEdge"]] = relationship(
        "WorldGraphEdge",
        back_populates="source_node",
        foreign_keys="WorldGraphEdge.source_node_id",
        cascade="all, delete-orphan"
    )
    incoming_edges: Mapped[List["WorldGraphEdge"]] = relationship(
        "WorldGraphEdge",
        back_populates="target_node",
        foreign_keys="WorldGraphEdge.target_node_id",
        cascade="all, delete-orphan"
    )

    # Indexes and constraints
    __table_args__ = (
        Index('ix_world_graph_nodes_world_entity', 'world_id', 'entity_type', 'entity_id'),
        UniqueConstraint('world_id', 'entity_type', 'entity_id', name='uq_graph_node'),
    )

    # Valid entity types
    ENTITY_TYPES = ["character", "location", "event", "story", "beat"]

    def __repr__(self) -> str:
        return f"<WorldGraphNode(id={self.id}, type={self.entity_type}, entity_id={self.entity_id})>"


class WorldGraphEdge(Base):
    """
    Edge representing relationships between entities in the knowledge graph.

    Captures various relationship types including explicit relationships
    (knows, located_at) and computed relationships (semantic_similarity).

    Attributes:
        id: Unique identifier
        world_id: Foreign key to world
        source_node_id: Source node ID
        target_node_id: Target node ID
        relationship_type: Type of relationship
        strength: Edge strength/weight (0.0 to 1.0)
        edge_metadata: Additional metadata for the relationship
        created_at: Timestamp of creation
    """
    __tablename__ = "world_graph_edges"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        comment="Edge UUID"
    )

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="World ID"
    )

    source_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("world_graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source node ID"
    )

    target_node_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("world_graph_nodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target node ID"
    )

    relationship_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Relationship type: mentions, knows, located_at, causes, semantic_similar"
    )

    strength: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
        comment="Edge strength/weight (0.0 to 1.0)"
    )

    edge_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata",  # Column name in database
        JSON,
        nullable=True,
        comment="Additional metadata"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp of creation"
    )

    # Relationships
    world: Mapped["World"] = relationship("World", back_populates="graph_edges")
    source_node: Mapped["WorldGraphNode"] = relationship(
        "WorldGraphNode",
        back_populates="outgoing_edges",
        foreign_keys=[source_node_id]
    )
    target_node: Mapped["WorldGraphNode"] = relationship(
        "WorldGraphNode",
        back_populates="incoming_edges",
        foreign_keys=[target_node_id]
    )

    # Indexes
    __table_args__ = (
        Index('ix_graph_edges_source_target', 'source_node_id', 'target_node_id'),
    )

    # Valid relationship types
    RELATIONSHIP_TYPES = [
        "mentions",           # Beat -> Character/Location
        "appears_in",         # Character -> Beat
        "located_at",         # Event -> Location
        "knows",              # Character -> Character
        "causes",             # Event -> Event
        "semantic_similar",   # Any -> Any (embedding similarity)
        "temporal_proximity", # Event -> Event
        "contains",           # Story -> Beat
        "part_of",            # Beat -> Story
    ]

    def __repr__(self) -> str:
        return f"<WorldGraphEdge(id={self.id}, type={self.relationship_type}, source={self.source_node_id}, target={self.target_node_id})>"


class WorldGraphSyncStatus(Base):
    """
    Track GraphRAG sync state per world.

    Monitors the synchronization status of the knowledge graph,
    including last sync times and error tracking.

    Attributes:
        world_id: Foreign key to world (primary key)
        last_full_sync: Timestamp of last full graph rebuild
        last_incremental_sync: Timestamp of last incremental update
        node_count: Current number of nodes in graph
        edge_count: Current number of edges in graph
        sync_in_progress: Whether a sync is currently running
        last_error: Last sync error message (if any)
    """
    __tablename__ = "world_graph_sync_status"

    world_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("worlds.id", ondelete="CASCADE"),
        primary_key=True,
        comment="World ID (primary key)"
    )

    last_full_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last full graph rebuild"
    )

    last_incremental_sync: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last incremental update"
    )

    node_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current number of nodes"
    )

    edge_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Current number of edges"
    )

    sync_in_progress: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether sync is currently running"
    )

    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Last sync error message"
    )

    # Relationships
    world: Mapped["World"] = relationship("World", back_populates="graph_sync_status")

    def __repr__(self) -> str:
        return f"<WorldGraphSyncStatus(world_id={self.world_id}, nodes={self.node_count}, edges={self.edge_count})>"
