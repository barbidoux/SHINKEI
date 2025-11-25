"""GraphRAG repository for database operations on world knowledge graph."""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from shinkei.models.graph_rag import WorldGraphNode, WorldGraphEdge, WorldGraphSyncStatus
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class GraphRAGRepository:
    """Repository for GraphRAG model database operations."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self.session = session

    # ========================
    # NODE OPERATIONS
    # ========================

    async def create_node(
        self,
        world_id: str,
        entity_type: str,
        entity_id: str,
        content_hash: str,
        embedding: Optional[List[float]] = None,
        semantic_summary: Optional[str] = None,
        importance_score: float = 0.0
    ) -> WorldGraphNode:
        """
        Create a new graph node.

        Args:
            world_id: World ID
            entity_type: Type of entity (character, location, etc.)
            entity_id: ID of the referenced entity
            content_hash: Hash of source content
            embedding: Vector embedding
            semantic_summary: AI-generated summary
            importance_score: PageRank-like score

        Returns:
            Created node instance
        """
        if entity_type not in WorldGraphNode.ENTITY_TYPES:
            raise ValueError(f"Invalid entity_type: {entity_type}")

        node = WorldGraphNode(
            world_id=world_id,
            entity_type=entity_type,
            entity_id=entity_id,
            content_hash=content_hash,
            embedding=embedding,
            semantic_summary=semantic_summary,
            importance_score=importance_score,
        )

        self.session.add(node)
        await self.session.flush()
        await self.session.refresh(node)

        logger.debug("graph_node_created", node_id=node.id, entity_type=entity_type, entity_id=entity_id)
        return node

    async def get_node_by_id(self, node_id: str) -> Optional[WorldGraphNode]:
        """Get a graph node by its ID."""
        result = await self.session.execute(
            select(WorldGraphNode).where(WorldGraphNode.id == node_id)
        )
        return result.scalar_one_or_none()

    async def get_node_by_entity(
        self,
        world_id: str,
        entity_type: str,
        entity_id: str
    ) -> Optional[WorldGraphNode]:
        """
        Get a graph node by entity reference.

        Args:
            world_id: World ID
            entity_type: Entity type
            entity_id: Entity ID

        Returns:
            Node instance or None
        """
        result = await self.session.execute(
            select(WorldGraphNode).where(
                WorldGraphNode.world_id == world_id,
                WorldGraphNode.entity_type == entity_type,
                WorldGraphNode.entity_id == entity_id
            )
        )
        return result.scalar_one_or_none()

    async def upsert_node(
        self,
        world_id: str,
        entity_type: str,
        entity_id: str,
        content_hash: str,
        embedding: Optional[List[float]] = None,
        semantic_summary: Optional[str] = None,
        importance_score: Optional[float] = None
    ) -> WorldGraphNode:
        """
        Create or update a graph node.

        Args:
            world_id: World ID
            entity_type: Type of entity
            entity_id: ID of the referenced entity
            content_hash: Hash of source content
            embedding: Vector embedding
            semantic_summary: AI-generated summary
            importance_score: PageRank-like score

        Returns:
            Created or updated node instance
        """
        existing = await self.get_node_by_entity(world_id, entity_type, entity_id)

        if existing:
            # Update if content changed
            if existing.content_hash != content_hash:
                existing.content_hash = content_hash
                if embedding is not None:
                    existing.embedding = embedding
                if semantic_summary is not None:
                    existing.semantic_summary = semantic_summary
                if importance_score is not None:
                    existing.importance_score = importance_score

                await self.session.flush()
                await self.session.refresh(existing)

            return existing
        else:
            return await self.create_node(
                world_id=world_id,
                entity_type=entity_type,
                entity_id=entity_id,
                content_hash=content_hash,
                embedding=embedding,
                semantic_summary=semantic_summary,
                importance_score=importance_score or 0.0
            )

    async def list_nodes_by_world(
        self,
        world_id: str,
        entity_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[WorldGraphNode], int]:
        """
        List graph nodes in a world.

        Args:
            world_id: World ID
            entity_type: Filter by entity type (optional)
            skip: Number to skip
            limit: Max to return

        Returns:
            Tuple of (nodes list, total count)
        """
        query = select(WorldGraphNode).where(WorldGraphNode.world_id == world_id)

        if entity_type:
            query = query.where(WorldGraphNode.entity_type == entity_type)

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar_one()

        query = query.order_by(WorldGraphNode.importance_score.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        nodes = list(result.scalars().all())

        return nodes, total

    async def delete_node(self, node_id: str) -> bool:
        """Delete a graph node."""
        node = await self.get_node_by_id(node_id)
        if not node:
            return False

        await self.session.delete(node)
        await self.session.flush()
        return True

    async def delete_nodes_by_entity(
        self,
        world_id: str,
        entity_type: str,
        entity_id: str
    ) -> int:
        """
        Delete graph nodes for a specific entity.

        Returns:
            Number of deleted nodes
        """
        result = await self.session.execute(
            delete(WorldGraphNode).where(
                WorldGraphNode.world_id == world_id,
                WorldGraphNode.entity_type == entity_type,
                WorldGraphNode.entity_id == entity_id
            )
        )
        await self.session.flush()
        return result.rowcount

    # ========================
    # EDGE OPERATIONS
    # ========================

    async def create_edge(
        self,
        world_id: str,
        source_node_id: str,
        target_node_id: str,
        relationship_type: str,
        strength: float = 1.0,
        edge_metadata: Optional[dict] = None
    ) -> WorldGraphEdge:
        """
        Create a new graph edge.

        Args:
            world_id: World ID
            source_node_id: Source node ID
            target_node_id: Target node ID
            relationship_type: Type of relationship
            strength: Edge strength (0.0 to 1.0)
            edge_metadata: Additional metadata

        Returns:
            Created edge instance
        """
        edge = WorldGraphEdge(
            world_id=world_id,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            relationship_type=relationship_type,
            strength=strength,
            edge_metadata=edge_metadata,
        )

        self.session.add(edge)
        await self.session.flush()
        await self.session.refresh(edge)

        logger.debug("graph_edge_created", edge_id=edge.id, type=relationship_type)
        return edge

    async def get_edge_by_id(self, edge_id: str) -> Optional[WorldGraphEdge]:
        """Get an edge by ID."""
        result = await self.session.execute(
            select(WorldGraphEdge).where(WorldGraphEdge.id == edge_id)
        )
        return result.scalar_one_or_none()

    async def get_edges_from_node(
        self,
        node_id: str,
        relationship_type: Optional[str] = None
    ) -> list[WorldGraphEdge]:
        """
        Get all outgoing edges from a node.

        Args:
            node_id: Source node ID
            relationship_type: Filter by type (optional)

        Returns:
            List of edges
        """
        query = select(WorldGraphEdge).where(WorldGraphEdge.source_node_id == node_id)

        if relationship_type:
            query = query.where(WorldGraphEdge.relationship_type == relationship_type)

        result = await self.session.execute(query.order_by(WorldGraphEdge.strength.desc()))
        return list(result.scalars().all())

    async def get_edges_to_node(
        self,
        node_id: str,
        relationship_type: Optional[str] = None
    ) -> list[WorldGraphEdge]:
        """
        Get all incoming edges to a node.

        Args:
            node_id: Target node ID
            relationship_type: Filter by type (optional)

        Returns:
            List of edges
        """
        query = select(WorldGraphEdge).where(WorldGraphEdge.target_node_id == node_id)

        if relationship_type:
            query = query.where(WorldGraphEdge.relationship_type == relationship_type)

        result = await self.session.execute(query.order_by(WorldGraphEdge.strength.desc()))
        return list(result.scalars().all())

    async def find_connected_nodes(
        self,
        node_id: str,
        depth: int = 1,
        relationship_types: Optional[List[str]] = None
    ) -> list[WorldGraphNode]:
        """
        Find all nodes connected to a node within a given depth.

        Args:
            node_id: Starting node ID
            depth: Maximum traversal depth
            relationship_types: Filter by relationship types

        Returns:
            List of connected nodes
        """
        visited = set()
        to_visit = {node_id}
        connected = []

        for _ in range(depth):
            next_visit = set()
            for current_id in to_visit:
                if current_id in visited:
                    continue
                visited.add(current_id)

                # Get outgoing edges
                outgoing = await self.get_edges_from_node(current_id)
                for edge in outgoing:
                    if relationship_types and edge.relationship_type not in relationship_types:
                        continue
                    if edge.target_node_id not in visited:
                        next_visit.add(edge.target_node_id)

                # Get incoming edges
                incoming = await self.get_edges_to_node(current_id)
                for edge in incoming:
                    if relationship_types and edge.relationship_type not in relationship_types:
                        continue
                    if edge.source_node_id not in visited:
                        next_visit.add(edge.source_node_id)

            to_visit = next_visit

        # Fetch all connected nodes (excluding starting node)
        visited.discard(node_id)
        for nid in visited:
            node = await self.get_node_by_id(nid)
            if node:
                connected.append(node)

        return connected

    async def delete_edge(self, edge_id: str) -> bool:
        """Delete an edge."""
        edge = await self.get_edge_by_id(edge_id)
        if not edge:
            return False

        await self.session.delete(edge)
        await self.session.flush()
        return True

    async def delete_edges_for_node(self, node_id: str) -> int:
        """
        Delete all edges connected to a node.

        Returns:
            Number of deleted edges
        """
        result1 = await self.session.execute(
            delete(WorldGraphEdge).where(WorldGraphEdge.source_node_id == node_id)
        )
        result2 = await self.session.execute(
            delete(WorldGraphEdge).where(WorldGraphEdge.target_node_id == node_id)
        )
        await self.session.flush()
        return result1.rowcount + result2.rowcount

    # ========================
    # SYNC STATUS OPERATIONS
    # ========================

    async def get_sync_status(self, world_id: str) -> Optional[WorldGraphSyncStatus]:
        """Get sync status for a world."""
        result = await self.session.execute(
            select(WorldGraphSyncStatus).where(WorldGraphSyncStatus.world_id == world_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create_sync_status(self, world_id: str) -> WorldGraphSyncStatus:
        """Get or create sync status for a world."""
        status = await self.get_sync_status(world_id)
        if status:
            return status

        status = WorldGraphSyncStatus(
            world_id=world_id,
            node_count=0,
            edge_count=0,
            sync_in_progress=False,
        )
        self.session.add(status)
        await self.session.flush()
        await self.session.refresh(status)
        return status

    async def update_sync_status(
        self,
        world_id: str,
        last_full_sync: Optional[datetime] = None,
        last_incremental_sync: Optional[datetime] = None,
        node_count: Optional[int] = None,
        edge_count: Optional[int] = None,
        sync_in_progress: Optional[bool] = None,
        last_error: Optional[str] = None
    ) -> Optional[WorldGraphSyncStatus]:
        """
        Update sync status for a world.

        Args:
            world_id: World ID
            last_full_sync: Timestamp of last full sync
            last_incremental_sync: Timestamp of last incremental sync
            node_count: Current node count
            edge_count: Current edge count
            sync_in_progress: Whether sync is in progress
            last_error: Last error message

        Returns:
            Updated status or None if not found
        """
        status = await self.get_or_create_sync_status(world_id)

        if last_full_sync is not None:
            status.last_full_sync = last_full_sync
        if last_incremental_sync is not None:
            status.last_incremental_sync = last_incremental_sync
        if node_count is not None:
            status.node_count = node_count
        if edge_count is not None:
            status.edge_count = edge_count
        if sync_in_progress is not None:
            status.sync_in_progress = sync_in_progress
        if last_error is not None:
            status.last_error = last_error

        await self.session.flush()
        await self.session.refresh(status)
        return status

    async def start_sync(self, world_id: str) -> bool:
        """
        Mark sync as started for a world.

        Returns:
            True if started, False if already in progress
        """
        status = await self.get_or_create_sync_status(world_id)

        if status.sync_in_progress:
            return False

        status.sync_in_progress = True
        status.last_error = None
        await self.session.flush()
        return True

    async def finish_sync(
        self,
        world_id: str,
        is_full_sync: bool,
        error: Optional[str] = None
    ) -> WorldGraphSyncStatus:
        """
        Mark sync as finished for a world.

        Args:
            world_id: World ID
            is_full_sync: Whether this was a full sync
            error: Error message if sync failed

        Returns:
            Updated status
        """
        status = await self.get_or_create_sync_status(world_id)

        status.sync_in_progress = False
        status.last_error = error

        if not error:
            now = datetime.utcnow()
            if is_full_sync:
                status.last_full_sync = now
            status.last_incremental_sync = now

            # Update counts
            node_count = await self.session.execute(
                select(func.count()).where(WorldGraphNode.world_id == world_id)
            )
            status.node_count = node_count.scalar_one()

            edge_count = await self.session.execute(
                select(func.count()).where(WorldGraphEdge.world_id == world_id)
            )
            status.edge_count = edge_count.scalar_one()

        await self.session.flush()
        await self.session.refresh(status)
        return status

    # ========================
    # BULK OPERATIONS
    # ========================

    async def clear_world_graph(self, world_id: str) -> dict:
        """
        Clear all graph data for a world.

        Returns:
            Dict with counts of deleted items
        """
        # Delete edges first (FK constraint)
        edge_result = await self.session.execute(
            delete(WorldGraphEdge).where(WorldGraphEdge.world_id == world_id)
        )

        # Delete nodes
        node_result = await self.session.execute(
            delete(WorldGraphNode).where(WorldGraphNode.world_id == world_id)
        )

        # Update sync status
        await self.update_sync_status(world_id, node_count=0, edge_count=0)

        await self.session.flush()

        logger.info(
            "world_graph_cleared",
            world_id=world_id,
            nodes_deleted=node_result.rowcount,
            edges_deleted=edge_result.rowcount
        )

        return {
            "nodes_deleted": node_result.rowcount,
            "edges_deleted": edge_result.rowcount
        }
