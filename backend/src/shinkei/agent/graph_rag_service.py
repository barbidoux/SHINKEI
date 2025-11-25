"""GraphRAG Service for Story Pilot AI Chat Assistant.

This service handles the knowledge graph operations including:
- Building graphs from world entities
- Generating embeddings for semantic search
- Graph traversal and querying
- Incremental sync with change detection
"""
import hashlib
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.repositories.graph_rag import GraphRAGRepository
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.location import LocationRepository
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.repositories.character_relationship import CharacterRelationshipRepository
from shinkei.repositories.entity_mention import EntityMentionRepository
from shinkei.models.graph_rag import WorldGraphNode, WorldGraphEdge
from shinkei.generation.factory import ModelFactory
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class GraphContext:
    """Context for graph queries."""
    world_id: str
    story_id: Optional[str] = None
    beat_id: Optional[str] = None
    character_id: Optional[str] = None
    location_id: Optional[str] = None
    max_depth: int = 2
    max_results: int = 20


@dataclass
class SemanticSearchResult:
    """Result from semantic search."""
    node_id: str
    entity_type: str
    entity_id: str
    semantic_summary: Optional[str]
    importance_score: float
    relevance_score: float  # Cosine similarity or other distance
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphQueryResult:
    """Result from graph query."""
    nodes: List[WorldGraphNode]
    edges: List[WorldGraphEdge]
    paths: List[List[str]]  # Node ID paths
    metadata: Dict[str, Any] = field(default_factory=dict)


class GraphRAGService:
    """
    Service for GraphRAG operations.

    Handles building and querying the knowledge graph for semantic
    search and context retrieval.
    """

    # Embedding model configuration
    EMBEDDING_DIMENSION = 1536  # OpenAI text-embedding-3-small dimension
    EMBEDDING_MODEL = "text-embedding-3-small"

    def __init__(self, session: AsyncSession, provider: str = "openai"):
        """
        Initialize GraphRAG service.

        Args:
            session: SQLAlchemy async session
            provider: LLM provider for embeddings (openai, anthropic)
        """
        self.session = session
        self.provider = provider
        self.graph_repo = GraphRAGRepository(session)
        self._embedding_client = None

    async def _get_embedding_client(self):
        """Get or create embedding client."""
        if self._embedding_client is None:
            if self.provider == "openai":
                from openai import AsyncOpenAI
                from shinkei.config import settings
                self._embedding_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            elif self.provider == "anthropic":
                # Anthropic doesn't have embedding API, fall back to OpenAI
                from openai import AsyncOpenAI
                from shinkei.config import settings
                self._embedding_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            else:
                raise ValueError(f"Unsupported embedding provider: {self.provider}")
        return self._embedding_client

    # ========================
    # EMBEDDING GENERATION
    # ========================

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if not text or not text.strip():
            return []

        client = await self._get_embedding_client()

        try:
            # Truncate to avoid token limits (8191 tokens for text-embedding-3-small)
            truncated_text = text[:8000]

            response = await client.embeddings.create(
                model=self.EMBEDDING_MODEL,
                input=truncated_text,
                encoding_format="float"
            )

            embedding = response.data[0].embedding
            logger.debug("embedding_generated", text_length=len(text), dim=len(embedding))
            return embedding

        except Exception as e:
            logger.error("embedding_generation_error", error=str(e))
            return []

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per batch

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        client = await self._get_embedding_client()
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            # Truncate each text
            batch = [t[:8000] if t else "" for t in batch]

            try:
                response = await client.embeddings.create(
                    model=self.EMBEDDING_MODEL,
                    input=batch,
                    encoding_format="float"
                )

                for item in response.data:
                    embeddings.append(item.embedding)

                logger.debug(
                    "batch_embeddings_generated",
                    batch_num=i // batch_size + 1,
                    count=len(batch)
                )

            except Exception as e:
                logger.error("batch_embedding_error", error=str(e), batch=i)
                # Add empty embeddings for failed batch
                embeddings.extend([[] for _ in batch])

        return embeddings

    # ========================
    # CONTENT HASHING
    # ========================

    def compute_content_hash(self, content: str) -> str:
        """
        Compute SHA-256 hash of content for change detection.

        Args:
            content: Content to hash

        Returns:
            Hex-encoded hash
        """
        if not content:
            content = ""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def compute_entity_hash(self, entity: Any) -> str:
        """
        Compute hash for an entity based on its key fields.

        Args:
            entity: Entity object

        Returns:
            Content hash
        """
        if hasattr(entity, "content"):
            # Beat
            return self.compute_content_hash(entity.content)
        elif hasattr(entity, "description"):
            # Character, Location, World
            content = f"{getattr(entity, 'name', '')}\n{entity.description or ''}"
            return self.compute_content_hash(content)
        elif hasattr(entity, "summary"):
            # Event
            content = f"{entity.summary or ''}\n{getattr(entity, 'description', '') or ''}"
            return self.compute_content_hash(content)
        else:
            return self.compute_content_hash(str(entity.id))

    # ========================
    # SEMANTIC SUMMARY GENERATION
    # ========================

    async def generate_semantic_summary(
        self,
        entity_type: str,
        entity: Any
    ) -> str:
        """
        Generate semantic summary for an entity.

        Args:
            entity_type: Type of entity
            entity: Entity object

        Returns:
            Semantic summary text
        """
        try:
            model = ModelFactory.create(self.provider)

            if entity_type == "character":
                text = (
                    f"Character: {entity.name}\n"
                    f"Role: {entity.role or 'Unknown'}\n"
                    f"Importance: {entity.importance.value if entity.importance else 'Unknown'}\n"
                    f"Description: {entity.description or 'No description'}"
                )
            elif entity_type == "location":
                text = (
                    f"Location: {entity.name}\n"
                    f"Importance: {entity.importance.value if entity.importance else 'Unknown'}\n"
                    f"Description: {entity.description or 'No description'}"
                )
            elif entity_type == "event":
                text = (
                    f"Event: {entity.summary or 'Untitled'}\n"
                    f"Type: {entity.event_type.value if entity.event_type else 'Unknown'}\n"
                    f"Time: {entity.label_time or str(entity.t)}\n"
                    f"Description: {getattr(entity, 'description', '') or ''}"
                )
            elif entity_type == "story":
                text = (
                    f"Story: {entity.title}\n"
                    f"Synopsis: {entity.synopsis or 'No synopsis'}\n"
                    f"Theme: {entity.theme or 'Not specified'}\n"
                    f"Status: {entity.status.value if entity.status else 'Unknown'}"
                )
            elif entity_type == "beat":
                text = (
                    f"Beat (Order {entity.order_index}):\n"
                    f"Summary: {entity.summary or 'No summary'}\n"
                    f"Content Preview: {entity.content[:500] if entity.content else ''}"
                )
            else:
                text = str(entity)

            # Use LLM to generate concise semantic summary
            summary = await model.summarize(text)
            return summary

        except Exception as e:
            logger.error("semantic_summary_error", error=str(e), entity_type=entity_type)
            # Fallback to basic summary
            if hasattr(entity, "name"):
                return f"{entity_type.title()}: {entity.name}"
            elif hasattr(entity, "title"):
                return f"{entity_type.title()}: {entity.title}"
            elif hasattr(entity, "summary"):
                return entity.summary or ""
            return f"Unknown {entity_type}"

    # ========================
    # GRAPH BUILDING
    # ========================

    async def build_world_graph(
        self,
        world_id: str,
        full_rebuild: bool = False
    ) -> Dict[str, Any]:
        """
        Build or update the knowledge graph for a world.

        Args:
            world_id: World ID
            full_rebuild: If True, clear and rebuild entire graph

        Returns:
            Build statistics
        """
        # Check if sync is already in progress
        can_start = await self.graph_repo.start_sync(world_id)
        if not can_start:
            return {
                "status": "skipped",
                "reason": "Sync already in progress"
            }

        try:
            if full_rebuild:
                await self.graph_repo.clear_world_graph(world_id)

            stats = {
                "nodes_created": 0,
                "nodes_updated": 0,
                "edges_created": 0,
                "errors": []
            }

            # Build nodes for all entity types
            await self._build_character_nodes(world_id, stats)
            await self._build_location_nodes(world_id, stats)
            await self._build_event_nodes(world_id, stats)
            await self._build_story_nodes(world_id, stats)
            await self._build_beat_nodes(world_id, stats)

            # Build edges for relationships
            await self._build_relationship_edges(world_id, stats)
            await self._build_mention_edges(world_id, stats)
            await self._build_hierarchy_edges(world_id, stats)

            # Finish sync
            await self.graph_repo.finish_sync(
                world_id,
                is_full_sync=full_rebuild
            )

            logger.info(
                "world_graph_built",
                world_id=world_id,
                full_rebuild=full_rebuild,
                nodes_created=stats["nodes_created"],
                nodes_updated=stats["nodes_updated"],
                edges_created=stats["edges_created"]
            )

            return {
                "status": "completed",
                **stats
            }

        except Exception as e:
            logger.error("graph_build_error", world_id=world_id, error=str(e))
            await self.graph_repo.finish_sync(world_id, is_full_sync=full_rebuild, error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }

    async def _build_character_nodes(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build graph nodes for characters."""
        char_repo = CharacterRepository(self.session)
        characters, _ = await char_repo.list_by_world(world_id, limit=1000)

        texts_to_embed = []
        entities_to_process = []

        for char in characters:
            content_hash = self.compute_entity_hash(char)
            existing = await self.graph_repo.get_node_by_entity(
                world_id, "character", char.id
            )

            if existing and existing.content_hash == content_hash:
                continue  # No change

            # Prepare for batch embedding
            text = f"Character: {char.name}. {char.description or ''}"
            texts_to_embed.append(text)
            entities_to_process.append((char, content_hash, existing))

        # Generate embeddings in batch
        if texts_to_embed:
            embeddings = await self.generate_embeddings_batch(texts_to_embed)

            for i, (char, content_hash, existing) in enumerate(entities_to_process):
                try:
                    summary = await self.generate_semantic_summary("character", char)
                    importance = self._compute_character_importance(char)

                    await self.graph_repo.upsert_node(
                        world_id=world_id,
                        entity_type="character",
                        entity_id=char.id,
                        content_hash=content_hash,
                        embedding=embeddings[i] if i < len(embeddings) else None,
                        semantic_summary=summary,
                        importance_score=importance
                    )

                    if existing:
                        stats["nodes_updated"] += 1
                    else:
                        stats["nodes_created"] += 1

                except Exception as e:
                    stats["errors"].append(f"Character {char.id}: {str(e)}")

    async def _build_location_nodes(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build graph nodes for locations."""
        loc_repo = LocationRepository(self.session)
        locations, _ = await loc_repo.list_by_world(world_id, limit=1000)

        texts_to_embed = []
        entities_to_process = []

        for loc in locations:
            content_hash = self.compute_entity_hash(loc)
            existing = await self.graph_repo.get_node_by_entity(
                world_id, "location", loc.id
            )

            if existing and existing.content_hash == content_hash:
                continue

            text = f"Location: {loc.name}. {loc.description or ''}"
            texts_to_embed.append(text)
            entities_to_process.append((loc, content_hash, existing))

        if texts_to_embed:
            embeddings = await self.generate_embeddings_batch(texts_to_embed)

            for i, (loc, content_hash, existing) in enumerate(entities_to_process):
                try:
                    summary = await self.generate_semantic_summary("location", loc)
                    importance = self._compute_location_importance(loc)

                    await self.graph_repo.upsert_node(
                        world_id=world_id,
                        entity_type="location",
                        entity_id=loc.id,
                        content_hash=content_hash,
                        embedding=embeddings[i] if i < len(embeddings) else None,
                        semantic_summary=summary,
                        importance_score=importance
                    )

                    if existing:
                        stats["nodes_updated"] += 1
                    else:
                        stats["nodes_created"] += 1

                except Exception as e:
                    stats["errors"].append(f"Location {loc.id}: {str(e)}")

    async def _build_event_nodes(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build graph nodes for world events."""
        event_repo = WorldEventRepository(self.session)
        events, _ = await event_repo.list_by_world(world_id, limit=1000)

        texts_to_embed = []
        entities_to_process = []

        for event in events:
            content_hash = self.compute_entity_hash(event)
            existing = await self.graph_repo.get_node_by_entity(
                world_id, "event", event.id
            )

            if existing and existing.content_hash == content_hash:
                continue

            text = f"Event: {event.summary or 'Untitled'}. Time: {event.label_time or event.t}."
            texts_to_embed.append(text)
            entities_to_process.append((event, content_hash, existing))

        if texts_to_embed:
            embeddings = await self.generate_embeddings_batch(texts_to_embed)

            for i, (event, content_hash, existing) in enumerate(entities_to_process):
                try:
                    summary = await self.generate_semantic_summary("event", event)
                    importance = 0.5  # Events have moderate baseline importance

                    await self.graph_repo.upsert_node(
                        world_id=world_id,
                        entity_type="event",
                        entity_id=event.id,
                        content_hash=content_hash,
                        embedding=embeddings[i] if i < len(embeddings) else None,
                        semantic_summary=summary,
                        importance_score=importance
                    )

                    if existing:
                        stats["nodes_updated"] += 1
                    else:
                        stats["nodes_created"] += 1

                except Exception as e:
                    stats["errors"].append(f"Event {event.id}: {str(e)}")

    async def _build_story_nodes(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build graph nodes for stories."""
        story_repo = StoryRepository(self.session)
        stories, _ = await story_repo.list_by_world(world_id, limit=1000)

        texts_to_embed = []
        entities_to_process = []

        for story in stories:
            content_hash = self.compute_entity_hash(story)
            existing = await self.graph_repo.get_node_by_entity(
                world_id, "story", story.id
            )

            if existing and existing.content_hash == content_hash:
                continue

            text = f"Story: {story.title}. {story.synopsis or ''}"
            texts_to_embed.append(text)
            entities_to_process.append((story, content_hash, existing))

        if texts_to_embed:
            embeddings = await self.generate_embeddings_batch(texts_to_embed)

            for i, (story, content_hash, existing) in enumerate(entities_to_process):
                try:
                    summary = await self.generate_semantic_summary("story", story)
                    importance = 0.7  # Stories have high importance

                    await self.graph_repo.upsert_node(
                        world_id=world_id,
                        entity_type="story",
                        entity_id=story.id,
                        content_hash=content_hash,
                        embedding=embeddings[i] if i < len(embeddings) else None,
                        semantic_summary=summary,
                        importance_score=importance
                    )

                    if existing:
                        stats["nodes_updated"] += 1
                    else:
                        stats["nodes_created"] += 1

                except Exception as e:
                    stats["errors"].append(f"Story {story.id}: {str(e)}")

    async def _build_beat_nodes(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build graph nodes for story beats."""
        story_repo = StoryRepository(self.session)
        beat_repo = StoryBeatRepository(self.session)

        stories, _ = await story_repo.list_by_world(world_id, limit=1000)

        for story in stories:
            beats, _ = await beat_repo.list_by_story(story.id, limit=500)

            texts_to_embed = []
            entities_to_process = []

            for beat in beats:
                content_hash = self.compute_entity_hash(beat)
                existing = await self.graph_repo.get_node_by_entity(
                    world_id, "beat", beat.id
                )

                if existing and existing.content_hash == content_hash:
                    continue

                # Use summary or truncated content
                text = beat.summary or (beat.content[:500] if beat.content else "")
                texts_to_embed.append(text)
                entities_to_process.append((beat, content_hash, existing))

            if texts_to_embed:
                embeddings = await self.generate_embeddings_batch(texts_to_embed)

                for i, (beat, content_hash, existing) in enumerate(entities_to_process):
                    try:
                        summary = beat.summary or await self.generate_semantic_summary("beat", beat)
                        importance = 0.3  # Beats have lower individual importance

                        await self.graph_repo.upsert_node(
                            world_id=world_id,
                            entity_type="beat",
                            entity_id=beat.id,
                            content_hash=content_hash,
                            embedding=embeddings[i] if i < len(embeddings) else None,
                            semantic_summary=summary,
                            importance_score=importance
                        )

                        if existing:
                            stats["nodes_updated"] += 1
                        else:
                            stats["nodes_created"] += 1

                    except Exception as e:
                        stats["errors"].append(f"Beat {beat.id}: {str(e)}")

    async def _build_relationship_edges(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build edges for character relationships."""
        rel_repo = CharacterRelationshipRepository(self.session)
        relationships, _ = await rel_repo.list_by_world(world_id, limit=1000)

        for rel in relationships:
            # Get nodes for both characters
            node_a = await self.graph_repo.get_node_by_entity(
                world_id, "character", rel.character_a_id
            )
            node_b = await self.graph_repo.get_node_by_entity(
                world_id, "character", rel.character_b_id
            )

            if not node_a or not node_b:
                continue

            try:
                # Create bidirectional edge for "knows" relationships
                await self.graph_repo.create_edge(
                    world_id=world_id,
                    source_node_id=node_a.id,
                    target_node_id=node_b.id,
                    relationship_type="knows",
                    strength=0.8,
                    edge_metadata={
                        "relationship_type": rel.relationship_type,
                        "description": rel.description
                    }
                )
                stats["edges_created"] += 1

            except Exception as e:
                stats["errors"].append(f"Relationship {rel.id}: {str(e)}")

    async def _build_mention_edges(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build edges for entity mentions in beats."""
        mention_repo = EntityMentionRepository(self.session)
        beat_repo = StoryBeatRepository(self.session)
        story_repo = StoryRepository(self.session)

        stories, _ = await story_repo.list_by_world(world_id, limit=1000)

        for story in stories:
            beats, _ = await beat_repo.list_by_story(story.id, limit=500)

            for beat in beats:
                beat_node = await self.graph_repo.get_node_by_entity(
                    world_id, "beat", beat.id
                )
                if not beat_node:
                    continue

                mentions = await mention_repo.list_by_beat(beat.id)

                for mention in mentions:
                    entity_node = await self.graph_repo.get_node_by_entity(
                        world_id, mention.entity_type, mention.entity_id
                    )
                    if not entity_node:
                        continue

                    try:
                        # Beat mentions entity
                        await self.graph_repo.create_edge(
                            world_id=world_id,
                            source_node_id=beat_node.id,
                            target_node_id=entity_node.id,
                            relationship_type="mentions",
                            strength=0.7,
                            edge_metadata={"mention_type": mention.mention_type}
                        )
                        stats["edges_created"] += 1

                        # Entity appears_in beat
                        await self.graph_repo.create_edge(
                            world_id=world_id,
                            source_node_id=entity_node.id,
                            target_node_id=beat_node.id,
                            relationship_type="appears_in",
                            strength=0.7,
                            edge_metadata={"mention_type": mention.mention_type}
                        )
                        stats["edges_created"] += 1

                    except Exception as e:
                        stats["errors"].append(f"Mention edge {mention.id}: {str(e)}")

    async def _build_hierarchy_edges(self, world_id: str, stats: Dict[str, Any]) -> None:
        """Build edges for hierarchical relationships (location containment, story->beat)."""
        loc_repo = LocationRepository(self.session)
        story_repo = StoryRepository(self.session)
        beat_repo = StoryBeatRepository(self.session)

        # Location hierarchy
        locations, _ = await loc_repo.list_by_world(world_id, limit=1000)
        for loc in locations:
            if not loc.parent_id:
                continue

            child_node = await self.graph_repo.get_node_by_entity(
                world_id, "location", loc.id
            )
            parent_node = await self.graph_repo.get_node_by_entity(
                world_id, "location", loc.parent_id
            )

            if child_node and parent_node:
                try:
                    await self.graph_repo.create_edge(
                        world_id=world_id,
                        source_node_id=parent_node.id,
                        target_node_id=child_node.id,
                        relationship_type="contains",
                        strength=1.0
                    )
                    stats["edges_created"] += 1

                except Exception as e:
                    stats["errors"].append(f"Location hierarchy {loc.id}: {str(e)}")

        # Story -> Beat containment
        stories, _ = await story_repo.list_by_world(world_id, limit=1000)
        for story in stories:
            story_node = await self.graph_repo.get_node_by_entity(
                world_id, "story", story.id
            )
            if not story_node:
                continue

            beats, _ = await beat_repo.list_by_story(story.id, limit=500)
            for beat in beats:
                beat_node = await self.graph_repo.get_node_by_entity(
                    world_id, "beat", beat.id
                )
                if not beat_node:
                    continue

                try:
                    # Story contains beat
                    await self.graph_repo.create_edge(
                        world_id=world_id,
                        source_node_id=story_node.id,
                        target_node_id=beat_node.id,
                        relationship_type="contains",
                        strength=1.0
                    )
                    # Beat is part_of story
                    await self.graph_repo.create_edge(
                        world_id=world_id,
                        source_node_id=beat_node.id,
                        target_node_id=story_node.id,
                        relationship_type="part_of",
                        strength=1.0
                    )
                    stats["edges_created"] += 2

                except Exception as e:
                    stats["errors"].append(f"Story->Beat {beat.id}: {str(e)}")

    def _compute_character_importance(self, character: Any) -> float:
        """Compute importance score for a character."""
        if character.importance:
            if character.importance.value == "major":
                return 0.9
            elif character.importance.value == "minor":
                return 0.5
            elif character.importance.value == "background":
                return 0.2
        return 0.5

    def _compute_location_importance(self, location: Any) -> float:
        """Compute importance score for a location."""
        if location.importance:
            if location.importance.value == "major":
                return 0.8
            elif location.importance.value == "minor":
                return 0.4
            elif location.importance.value == "background":
                return 0.2
        return 0.4

    # ========================
    # SEMANTIC SEARCH
    # ========================

    async def semantic_search(
        self,
        world_id: str,
        query: str,
        entity_types: Optional[List[str]] = None,
        limit: int = 10,
        min_score: float = 0.5
    ) -> List[SemanticSearchResult]:
        """
        Perform semantic search across world entities.

        Args:
            world_id: World ID
            query: Search query text
            entity_types: Filter by entity types (optional)
            limit: Maximum results
            min_score: Minimum similarity score

        Returns:
            List of search results ranked by relevance
        """
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)
        if not query_embedding:
            return []

        # Get all nodes (with embeddings) for the world
        nodes, _ = await self.graph_repo.list_nodes_by_world(
            world_id,
            entity_type=entity_types[0] if entity_types and len(entity_types) == 1 else None,
            limit=1000
        )

        # Filter by entity types if multiple specified
        if entity_types and len(entity_types) > 1:
            nodes = [n for n in nodes if n.entity_type in entity_types]

        # Compute similarities
        results = []
        for node in nodes:
            if not node.embedding:
                continue

            similarity = self._cosine_similarity(query_embedding, node.embedding)
            if similarity >= min_score:
                results.append(SemanticSearchResult(
                    node_id=node.id,
                    entity_type=node.entity_type,
                    entity_id=node.entity_id,
                    semantic_summary=node.semantic_summary,
                    importance_score=node.importance_score,
                    relevance_score=similarity
                ))

        # Sort by relevance (with importance as tiebreaker)
        results.sort(
            key=lambda r: (r.relevance_score, r.importance_score),
            reverse=True
        )

        return results[:limit]

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(b * b for b in vec2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    # ========================
    # GRAPH QUERIES
    # ========================

    async def find_related_entities(
        self,
        world_id: str,
        entity_type: str,
        entity_id: str,
        depth: int = 2,
        relationship_types: Optional[List[str]] = None
    ) -> GraphQueryResult:
        """
        Find entities related to a given entity through graph traversal.

        Args:
            world_id: World ID
            entity_type: Type of source entity
            entity_id: ID of source entity
            depth: Maximum traversal depth
            relationship_types: Filter by relationship types

        Returns:
            Graph query result with nodes and edges
        """
        # Get source node
        source_node = await self.graph_repo.get_node_by_entity(
            world_id, entity_type, entity_id
        )
        if not source_node:
            return GraphQueryResult(nodes=[], edges=[], paths=[])

        # Find connected nodes
        connected = await self.graph_repo.find_connected_nodes(
            source_node.id,
            depth=depth,
            relationship_types=relationship_types
        )

        # Get edges between nodes
        all_edges = []
        node_ids = {source_node.id} | {n.id for n in connected}

        for node_id in node_ids:
            edges = await self.graph_repo.get_edges_from_node(node_id)
            for edge in edges:
                if edge.target_node_id in node_ids:
                    all_edges.append(edge)

        return GraphQueryResult(
            nodes=[source_node] + connected,
            edges=all_edges,
            paths=[],  # Paths can be computed if needed
            metadata={
                "source_entity": entity_id,
                "source_type": entity_type,
                "depth": depth
            }
        )

    async def get_context_for_beat(
        self,
        world_id: str,
        beat_id: str,
        max_entities: int = 10
    ) -> Dict[str, Any]:
        """
        Get relevant context for a beat from the knowledge graph.

        This is used by the agent to understand what entities
        are related to a specific beat.

        Args:
            world_id: World ID
            beat_id: Beat ID
            max_entities: Maximum related entities to return

        Returns:
            Context dictionary with related entities
        """
        # Get beat node
        beat_node = await self.graph_repo.get_node_by_entity(
            world_id, "beat", beat_id
        )
        if not beat_node:
            return {"error": "Beat not found in graph"}

        # Get directly connected entities
        related = await self.find_related_entities(
            world_id, "beat", beat_id, depth=1
        )

        # Organize by type
        context = {
            "beat_id": beat_id,
            "beat_summary": beat_node.semantic_summary,
            "characters": [],
            "locations": [],
            "events": [],
            "related_beats": []
        }

        for node in related.nodes:
            if node.entity_type == "character":
                context["characters"].append({
                    "id": node.entity_id,
                    "summary": node.semantic_summary,
                    "importance": node.importance_score
                })
            elif node.entity_type == "location":
                context["locations"].append({
                    "id": node.entity_id,
                    "summary": node.semantic_summary,
                    "importance": node.importance_score
                })
            elif node.entity_type == "event":
                context["events"].append({
                    "id": node.entity_id,
                    "summary": node.semantic_summary
                })
            elif node.entity_type == "beat" and node.entity_id != beat_id:
                context["related_beats"].append({
                    "id": node.entity_id,
                    "summary": node.semantic_summary
                })

        # Limit results
        for key in ["characters", "locations", "events", "related_beats"]:
            context[key] = context[key][:max_entities]

        return context

    async def get_character_story_arc(
        self,
        world_id: str,
        character_id: str,
        story_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a character's story arc across beats.

        Args:
            world_id: World ID
            character_id: Character ID
            story_id: Limit to specific story (optional)

        Returns:
            Character arc data
        """
        # Get character node
        char_node = await self.graph_repo.get_node_by_entity(
            world_id, "character", character_id
        )
        if not char_node:
            return {"error": "Character not found"}

        # Get all beats where character appears
        edges = await self.graph_repo.get_edges_from_node(
            char_node.id,
            relationship_type="appears_in"
        )

        beats = []
        for edge in edges:
            beat_node = await self.graph_repo.get_node_by_id(edge.target_node_id)
            if beat_node and beat_node.entity_type == "beat":
                # Check if in requested story
                if story_id:
                    # Would need to check beat.story_id - simplified for now
                    pass
                beats.append({
                    "beat_id": beat_node.entity_id,
                    "summary": beat_node.semantic_summary
                })

        return {
            "character_id": character_id,
            "character_summary": char_node.semantic_summary,
            "appearances": len(beats),
            "beats": beats
        }
