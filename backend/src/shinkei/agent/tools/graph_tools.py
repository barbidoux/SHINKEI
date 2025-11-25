"""Graph tools for Story Pilot agent.

These tools allow the agent to perform semantic search and
graph queries on the world knowledge graph.
"""
from typing import Dict, Any, Optional, List
from shinkei.agent.tools.registry import tool, ToolCategory
from shinkei.agent.tools.context import ToolContext
from shinkei.agent.graph_rag_service import GraphRAGService


@tool(
    name="semantic_search",
    description="Search for entities in the world using natural language. Returns relevant characters, locations, events, stories, and beats based on semantic similarity.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query (e.g., 'characters involved in the war', 'mysterious locations')"
            },
            "entity_types": {
                "type": "array",
                "items": {"type": "string", "enum": ["character", "location", "event", "story", "beat"]},
                "description": "Filter results to specific entity types. If not provided, searches all types."
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 10
            }
        },
        "required": ["query"]
    },
    category=ToolCategory.GRAPH
)
async def semantic_search(
    context: ToolContext,
    query: str,
    entity_types: Optional[List[str]] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """Perform semantic search across world entities."""
    world_id = context.require_world()

    service = GraphRAGService(context.session)
    results = await service.semantic_search(
        world_id=world_id,
        query=query,
        entity_types=entity_types,
        limit=limit
    )

    return {
        "query": query,
        "results": [
            {
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "summary": r.semantic_summary,
                "relevance_score": round(r.relevance_score, 3),
                "importance_score": round(r.importance_score, 3)
            }
            for r in results
        ],
        "count": len(results)
    }


@tool(
    name="find_related_entities",
    description="Find entities related to a specific entity through the knowledge graph. Discovers connections like characters who appear together, locations where events happen, etc.",
    parameters={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "enum": ["character", "location", "event", "story", "beat"],
                "description": "Type of the source entity"
            },
            "entity_id": {
                "type": "string",
                "description": "ID of the source entity"
            },
            "depth": {
                "type": "integer",
                "description": "How many relationship hops to traverse",
                "default": 2
            },
            "relationship_types": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Filter by relationship types (mentions, knows, located_at, etc.)"
            }
        },
        "required": ["entity_type", "entity_id"]
    },
    category=ToolCategory.GRAPH
)
async def find_related_entities(
    context: ToolContext,
    entity_type: str,
    entity_id: str,
    depth: int = 2,
    relationship_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Find entities related through graph traversal."""
    world_id = context.require_world()

    service = GraphRAGService(context.session)
    result = await service.find_related_entities(
        world_id=world_id,
        entity_type=entity_type,
        entity_id=entity_id,
        depth=depth,
        relationship_types=relationship_types
    )

    # Format nodes by type
    by_type = {}
    for node in result.nodes:
        if node.entity_type not in by_type:
            by_type[node.entity_type] = []
        by_type[node.entity_type].append({
            "entity_id": node.entity_id,
            "summary": node.semantic_summary,
            "importance": round(node.importance_score, 3)
        })

    # Format edges
    edges = [
        {
            "source": e.source_node_id,
            "target": e.target_node_id,
            "type": e.relationship_type,
            "strength": round(e.strength, 3)
        }
        for e in result.edges
    ]

    return {
        "source": {"type": entity_type, "id": entity_id},
        "related_entities": by_type,
        "relationships": edges,
        "total_nodes": len(result.nodes),
        "total_edges": len(result.edges)
    }


@tool(
    name="get_beat_context",
    description="Get rich context for a specific beat from the knowledge graph. Returns all characters, locations, and events related to the beat.",
    parameters={
        "type": "object",
        "properties": {
            "beat_id": {
                "type": "string",
                "description": "Beat ID to get context for"
            },
            "max_entities": {
                "type": "integer",
                "description": "Maximum entities per type to return",
                "default": 10
            }
        },
        "required": ["beat_id"]
    },
    category=ToolCategory.GRAPH
)
async def get_beat_context(
    context: ToolContext,
    beat_id: str,
    max_entities: int = 10
) -> Dict[str, Any]:
    """Get context for a beat from the knowledge graph."""
    world_id = context.require_world()

    service = GraphRAGService(context.session)
    result = await service.get_context_for_beat(
        world_id=world_id,
        beat_id=beat_id,
        max_entities=max_entities
    )

    return result


@tool(
    name="get_character_arc",
    description="Get a character's story arc - all the beats where they appear and how their story progresses.",
    parameters={
        "type": "object",
        "properties": {
            "character_id": {
                "type": "string",
                "description": "Character ID"
            },
            "story_id": {
                "type": "string",
                "description": "Limit to a specific story (optional)"
            }
        },
        "required": ["character_id"]
    },
    category=ToolCategory.GRAPH
)
async def get_character_arc(
    context: ToolContext,
    character_id: str,
    story_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get character's story arc."""
    world_id = context.require_world()

    service = GraphRAGService(context.session)
    result = await service.get_character_story_arc(
        world_id=world_id,
        character_id=character_id,
        story_id=story_id
    )

    return result


@tool(
    name="build_world_graph",
    description="Build or update the knowledge graph for the current world. Use this to ensure the graph is up to date before performing searches.",
    parameters={
        "type": "object",
        "properties": {
            "full_rebuild": {
                "type": "boolean",
                "description": "If true, clear and rebuild the entire graph. Otherwise, only update changed entities.",
                "default": False
            }
        },
        "required": []
    },
    requires_approval=True,  # Graph building can be expensive
    category=ToolCategory.GRAPH
)
async def build_world_graph(
    context: ToolContext,
    full_rebuild: bool = False
) -> Dict[str, Any]:
    """Build or update the world knowledge graph."""
    world_id = context.require_world()

    service = GraphRAGService(context.session)
    result = await service.build_world_graph(
        world_id=world_id,
        full_rebuild=full_rebuild
    )

    return result


@tool(
    name="get_graph_status",
    description="Get the current status of the world knowledge graph including sync times and counts.",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    },
    category=ToolCategory.GRAPH
)
async def get_graph_status(context: ToolContext) -> Dict[str, Any]:
    """Get world graph status."""
    world_id = context.require_world()

    from shinkei.repositories.graph_rag import GraphRAGRepository
    repo = GraphRAGRepository(context.session)
    status = await repo.get_or_create_sync_status(world_id)

    return {
        "world_id": world_id,
        "node_count": status.node_count,
        "edge_count": status.edge_count,
        "last_full_sync": status.last_full_sync.isoformat() if status.last_full_sync else None,
        "last_incremental_sync": status.last_incremental_sync.isoformat() if status.last_incremental_sync else None,
        "sync_in_progress": status.sync_in_progress,
        "last_error": status.last_error
    }


@tool(
    name="find_similar_entities",
    description="Find entities semantically similar to a given entity. Useful for finding related characters, similar locations, or connected events.",
    parameters={
        "type": "object",
        "properties": {
            "entity_type": {
                "type": "string",
                "enum": ["character", "location", "event", "story", "beat"],
                "description": "Type of source entity"
            },
            "entity_id": {
                "type": "string",
                "description": "ID of source entity"
            },
            "target_types": {
                "type": "array",
                "items": {"type": "string", "enum": ["character", "location", "event", "story", "beat"]},
                "description": "Types of entities to find (defaults to same type as source)"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results",
                "default": 5
            }
        },
        "required": ["entity_type", "entity_id"]
    },
    category=ToolCategory.GRAPH
)
async def find_similar_entities(
    context: ToolContext,
    entity_type: str,
    entity_id: str,
    target_types: Optional[List[str]] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """Find semantically similar entities."""
    world_id = context.require_world()

    # Get source node
    from shinkei.repositories.graph_rag import GraphRAGRepository
    repo = GraphRAGRepository(context.session)
    source_node = await repo.get_node_by_entity(world_id, entity_type, entity_id)

    if not source_node:
        return {"error": "Entity not found in graph"}

    if not source_node.embedding:
        return {"error": "Entity has no embedding - rebuild graph first"}

    # Use semantic search with the entity's summary as query
    service = GraphRAGService(context.session)

    # If no target types specified, use same type
    if not target_types:
        target_types = [entity_type]

    results = await service.semantic_search(
        world_id=world_id,
        query=source_node.semantic_summary or f"{entity_type} {entity_id}",
        entity_types=target_types,
        limit=limit + 1  # +1 because source will be included
    )

    # Filter out source entity
    results = [r for r in results if r.entity_id != entity_id][:limit]

    return {
        "source": {
            "type": entity_type,
            "id": entity_id,
            "summary": source_node.semantic_summary
        },
        "similar_entities": [
            {
                "entity_type": r.entity_type,
                "entity_id": r.entity_id,
                "summary": r.semantic_summary,
                "similarity": round(r.relevance_score, 3)
            }
            for r in results
        ]
    }


@tool(
    name="trace_event_chain",
    description="Trace causal chains between events - find what events led to or resulted from a given event.",
    parameters={
        "type": "object",
        "properties": {
            "event_id": {
                "type": "string",
                "description": "Event ID to trace from"
            },
            "direction": {
                "type": "string",
                "enum": ["causes", "caused_by", "both"],
                "description": "Direction to trace: 'causes' (forward), 'caused_by' (backward), or 'both'",
                "default": "both"
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum chain length to trace",
                "default": 3
            }
        },
        "required": ["event_id"]
    },
    category=ToolCategory.GRAPH
)
async def trace_event_chain(
    context: ToolContext,
    event_id: str,
    direction: str = "both",
    max_depth: int = 3
) -> Dict[str, Any]:
    """Trace causal chains between events."""
    world_id = context.require_world()

    from shinkei.repositories.graph_rag import GraphRAGRepository
    from shinkei.repositories.world_event import WorldEventRepository

    graph_repo = GraphRAGRepository(context.session)
    event_repo = WorldEventRepository(context.session)

    # Get source event
    source_event = await event_repo.get_by_id(event_id)
    if not source_event:
        return {"error": "Event not found"}

    source_node = await graph_repo.get_node_by_entity(world_id, "event", event_id)

    causes = []  # Events this event caused
    caused_by = []  # Events that caused this event

    if direction in ["causes", "both"] and source_node:
        # Find events this event caused
        rel_types = ["causes"]
        connected = await graph_repo.find_connected_nodes(
            source_node.id,
            depth=max_depth,
            relationship_types=rel_types
        )
        for node in connected:
            if node.entity_type == "event":
                event = await event_repo.get_by_id(node.entity_id)
                if event:
                    causes.append({
                        "id": event.id,
                        "summary": event.summary,
                        "t": event.t,
                        "label_time": event.label_time
                    })

    if direction in ["caused_by", "both"] and source_event.caused_by_ids:
        # Trace back through caused_by_ids
        to_process = list(source_event.caused_by_ids)
        depth = 0
        while to_process and depth < max_depth:
            next_level = []
            for eid in to_process:
                event = await event_repo.get_by_id(eid)
                if event:
                    caused_by.append({
                        "id": event.id,
                        "summary": event.summary,
                        "t": event.t,
                        "label_time": event.label_time,
                        "depth": depth + 1
                    })
                    if event.caused_by_ids:
                        next_level.extend(event.caused_by_ids)
            to_process = next_level
            depth += 1

    return {
        "event": {
            "id": source_event.id,
            "summary": source_event.summary,
            "t": source_event.t,
            "label_time": source_event.label_time
        },
        "causes": causes,
        "caused_by": caused_by
    }
