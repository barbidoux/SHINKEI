"""API endpoints for Story Pilot AI Chat Assistant."""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.database.engine import get_db
from shinkei.auth.dependencies import get_current_user
from shinkei.models.user import User
from shinkei.agent.agent_service import AgentService, AgentContext
from shinkei.repositories.agent_persona import AgentPersonaRepository
from shinkei.repositories.world_coherence import WorldCoherenceRepository
from shinkei.repositories.graph_rag import GraphRAGRepository
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


# ========================
# REQUEST/RESPONSE SCHEMAS
# ========================

class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=10000)
    context: dict = Field(default_factory=dict, description="Navigation context")


class CreateConversationRequest(BaseModel):
    """Request body for creating a conversation."""
    title: Optional[str] = Field(None, max_length=255)
    mode: str = Field("ask", pattern="^(plan|ask|auto)$")
    persona_id: Optional[str] = None
    provider_override: Optional[str] = None
    model_override: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Request body for approving/rejecting an action."""
    message_id: str
    approved: bool


class ConversationResponse(BaseModel):
    """Response for a conversation."""
    id: str
    world_id: str
    title: Optional[str]
    mode: str
    persona_id: Optional[str]
    provider_override: Optional[str]
    model_override: Optional[str]
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    """Response for listing conversations."""
    conversations: List[ConversationResponse]
    total: int


class MessageResponse(BaseModel):
    """Response for a conversation message."""
    id: str
    role: str
    content: str
    reasoning: Optional[str] = None
    tool_calls: Optional[dict] = None
    tool_results: Optional[dict] = None
    pending_approval: bool
    created_at: str


class ConversationDetailResponse(BaseModel):
    """Response for a conversation with messages."""
    id: str
    world_id: str
    title: Optional[str]
    mode: str
    persona_id: Optional[str]
    provider_override: Optional[str]
    model_override: Optional[str]
    created_at: str
    updated_at: str
    messages: List[MessageResponse]


class CreatePersonaRequest(BaseModel):
    """Request body for creating a persona."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    system_prompt: str = Field(..., min_length=10)
    traits: Optional[dict] = Field(default_factory=dict)
    generation_defaults: Optional[dict] = Field(default_factory=dict)


class PersonaResponse(BaseModel):
    """Response for a persona."""
    id: str
    world_id: str
    name: str
    description: Optional[str]
    system_prompt: str
    traits: dict
    generation_defaults: dict
    is_builtin: bool
    is_active: bool


class PersonaListResponse(BaseModel):
    """Response for listing personas."""
    personas: List[PersonaResponse]
    total: int


class CoherenceSettingsRequest(BaseModel):
    """Request body for updating coherence settings."""
    time_consistency: Optional[str] = Field(None, pattern="^(strict|flexible|non-linear|irrelevant)$")
    spatial_consistency: Optional[str] = Field(None, pattern="^(euclidean|flexible|non-euclidean|irrelevant)$")
    causality: Optional[str] = Field(None, pattern="^(strict|flexible|paradox-allowed)$")
    character_knowledge: Optional[str] = Field(None, pattern="^(strict|flexible)$")
    death_permanence: Optional[str] = Field(None, pattern="^(permanent|reversible|fluid)$")
    custom_rules: Optional[List[str]] = None


class CoherenceSettingsResponse(BaseModel):
    """Response for coherence settings."""
    world_id: str
    time_consistency: str
    spatial_consistency: str
    causality: str
    character_knowledge: str
    death_permanence: str
    custom_rules: Optional[List[str]]


class GraphSyncStatusResponse(BaseModel):
    """Response for graph sync status."""
    world_id: str
    last_full_sync: Optional[str]
    last_incremental_sync: Optional[str]
    node_count: int
    edge_count: int
    sync_in_progress: bool
    last_error: Optional[str]


# ========================
# CHAT ENDPOINTS
# ========================

@router.post("/worlds/{world_id}/conversations/{conversation_id}/chat/stream")
async def chat_stream(
    world_id: str,
    conversation_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Stream chat response with the AI agent.

    This endpoint uses Server-Sent Events to stream the response
    in real-time, including tool execution events.
    """
    service = AgentService(db)

    # Build context from request
    context = AgentContext(
        world_id=world_id,
        story_id=request.context.get("story_id"),
        beat_id=request.context.get("beat_id"),
        character_id=request.context.get("character_id"),
        location_id=request.context.get("location_id"),
    )

    async def generate():
        async for event in service.chat(
            conversation_id=conversation_id,
            user_id=current_user.id,
            message=request.message,
            context=context
        ):
            yield event.to_sse()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/conversations/{conversation_id}/approve")
async def approve_action(
    conversation_id: str,
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """Approve or reject a pending action in Ask mode."""
    service = AgentService(db)

    async def generate():
        async for event in service.approve_action(
            conversation_id=conversation_id,
            user_id=current_user.id,
            message_id=request.message_id,
            approved=request.approved
        ):
            yield event.to_sse()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


# ========================
# CONVERSATION MANAGEMENT
# ========================

@router.get("/worlds/{world_id}/conversations", response_model=ConversationListResponse)
async def list_conversations(
    world_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all chat conversations for a world."""
    service = AgentService(db)
    conversations, total = await service.list_conversations(
        world_id=world_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit
    )

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=c.id,
                world_id=c.world_id,
                title=c.title,
                mode=c.mode,
                persona_id=c.persona_id,
                provider_override=c.provider_override,
                model_override=c.model_override,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in conversations
        ],
        total=total
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a conversation with all its messages."""
    from sqlalchemy import select
    from shinkei.models.conversation import Conversation, ConversationMessage

    # Get conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get messages
    messages_result = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conversation_id)
        .order_by(ConversationMessage.created_at)
    )
    messages = messages_result.scalars().all()

    return ConversationDetailResponse(
        id=conversation.id,
        world_id=conversation.world_id,
        title=conversation.title,
        mode=conversation.mode,
        persona_id=conversation.persona_id,
        provider_override=conversation.provider_override,
        model_override=conversation.model_override,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
        messages=[
            MessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                reasoning=m.reasoning,
                tool_calls=m.tool_calls,
                tool_results=m.tool_results,
                pending_approval=m.pending_approval,
                created_at=m.created_at.isoformat()
            )
            for m in messages
        ]
    )


@router.post("/worlds/{world_id}/conversations", response_model=ConversationResponse)
async def create_conversation(
    world_id: str,
    request: CreateConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat conversation."""
    service = AgentService(db)
    conversation = await service.get_or_create_conversation(
        world_id=world_id,
        user_id=current_user.id,
        title=request.title,
        mode=request.mode,
        persona_id=request.persona_id,
        provider_override=request.provider_override,
        model_override=request.model_override,
    )
    await db.commit()

    return ConversationResponse(
        id=conversation.id,
        world_id=conversation.world_id,
        title=conversation.title,
        mode=conversation.mode,
        persona_id=conversation.persona_id,
        provider_override=conversation.provider_override,
        model_override=conversation.model_override,
        created_at=conversation.created_at.isoformat(),
        updated_at=conversation.updated_at.isoformat(),
    )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a conversation."""
    service = AgentService(db)
    deleted = await service.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id
    )

    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.commit()
    return {"deleted": True}


# ========================
# PERSONA MANAGEMENT
# ========================

@router.get("/worlds/{world_id}/personas", response_model=PersonaListResponse)
async def list_personas(
    world_id: str,
    include_inactive: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List available personas for a world (builtin + user-created)."""
    repo = AgentPersonaRepository(db)

    # Ensure builtin personas exist
    await repo.ensure_builtin_personas(world_id)
    await db.commit()

    personas, total = await repo.list_by_world(
        world_id=world_id,
        include_inactive=include_inactive
    )

    return PersonaListResponse(
        personas=[
            PersonaResponse(
                id=p.id,
                world_id=p.world_id,
                name=p.name,
                description=p.description,
                system_prompt=p.system_prompt,
                traits=p.traits,
                generation_defaults=p.generation_defaults,
                is_builtin=p.is_builtin,
                is_active=p.is_active,
            )
            for p in personas
        ],
        total=total
    )


@router.post("/worlds/{world_id}/personas", response_model=PersonaResponse)
async def create_persona(
    world_id: str,
    request: CreatePersonaRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a custom agent persona."""
    repo = AgentPersonaRepository(db)

    # Check if name already exists
    existing = await repo.get_by_name(world_id, request.name)
    if existing:
        raise HTTPException(status_code=400, detail="Persona with this name already exists")

    persona = await repo.create(
        world_id=world_id,
        name=request.name,
        description=request.description,
        system_prompt=request.system_prompt,
        traits=request.traits,
        generation_defaults=request.generation_defaults,
        is_builtin=False
    )
    await db.commit()

    return PersonaResponse(
        id=persona.id,
        world_id=persona.world_id,
        name=persona.name,
        description=persona.description,
        system_prompt=persona.system_prompt,
        traits=persona.traits,
        generation_defaults=persona.generation_defaults,
        is_builtin=persona.is_builtin,
        is_active=persona.is_active,
    )


@router.delete("/personas/{persona_id}")
async def delete_persona(
    persona_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a custom persona (cannot delete builtin personas)."""
    repo = AgentPersonaRepository(db)
    deleted = await repo.delete(persona_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Persona not found or is builtin")

    await db.commit()
    return {"deleted": True}


# ========================
# COHERENCE SETTINGS
# ========================

@router.get("/worlds/{world_id}/coherence-settings", response_model=CoherenceSettingsResponse)
async def get_coherence_settings(
    world_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get coherence settings for a world."""
    repo = WorldCoherenceRepository(db)
    settings = await repo.get_or_create(world_id)
    await db.commit()

    return CoherenceSettingsResponse(
        world_id=settings.world_id,
        time_consistency=settings.time_consistency,
        spatial_consistency=settings.spatial_consistency,
        causality=settings.causality,
        character_knowledge=settings.character_knowledge,
        death_permanence=settings.death_permanence,
        custom_rules=settings.custom_rules,
    )


@router.put("/worlds/{world_id}/coherence-settings", response_model=CoherenceSettingsResponse)
async def update_coherence_settings(
    world_id: str,
    request: CoherenceSettingsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update coherence settings for a world."""
    repo = WorldCoherenceRepository(db)

    try:
        settings = await repo.update(
            world_id=world_id,
            time_consistency=request.time_consistency,
            spatial_consistency=request.spatial_consistency,
            causality=request.causality,
            character_knowledge=request.character_knowledge,
            death_permanence=request.death_permanence,
            custom_rules=request.custom_rules,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    await db.commit()

    return CoherenceSettingsResponse(
        world_id=settings.world_id,
        time_consistency=settings.time_consistency,
        spatial_consistency=settings.spatial_consistency,
        causality=settings.causality,
        character_knowledge=settings.character_knowledge,
        death_permanence=settings.death_permanence,
        custom_rules=settings.custom_rules,
    )


# ========================
# GRAPH RAG MANAGEMENT
# ========================

@router.get("/worlds/{world_id}/graph/status", response_model=GraphSyncStatusResponse)
async def get_graph_status(
    world_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get GraphRAG sync status for a world."""
    repo = GraphRAGRepository(db)
    status = await repo.get_or_create_sync_status(world_id)
    await db.commit()

    return GraphSyncStatusResponse(
        world_id=status.world_id,
        last_full_sync=status.last_full_sync.isoformat() if status.last_full_sync else None,
        last_incremental_sync=status.last_incremental_sync.isoformat() if status.last_incremental_sync else None,
        node_count=status.node_count,
        edge_count=status.edge_count,
        sync_in_progress=status.sync_in_progress,
        last_error=status.last_error,
    )


@router.post("/worlds/{world_id}/graph/sync")
async def sync_world_graph(
    world_id: str,
    full: bool = Query(False, description="Perform full rebuild instead of incremental"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger GraphRAG sync for a world.

    This endpoint builds or updates the knowledge graph with embeddings.
    """
    from shinkei.agent.graph_rag_service import GraphRAGService

    service = GraphRAGService(db)
    result = await service.build_world_graph(
        world_id=world_id,
        full_rebuild=full
    )
    await db.commit()

    return result


@router.delete("/worlds/{world_id}/graph")
async def clear_world_graph(
    world_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear all GraphRAG data for a world (useful for rebuild)."""
    repo = GraphRAGRepository(db)
    result = await repo.clear_world_graph(world_id)
    await db.commit()

    return result


# ========================
# SEMANTIC SEARCH
# ========================

class SemanticSearchRequest(BaseModel):
    """Request body for semantic search."""
    query: str = Field(..., min_length=1, max_length=1000)
    entity_types: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=100)


class SemanticSearchResultItem(BaseModel):
    """Single search result item."""
    entity_type: str
    entity_id: str
    summary: Optional[str]
    relevance_score: float
    importance_score: float


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""
    query: str
    results: List[SemanticSearchResultItem]
    total: int


@router.post("/worlds/{world_id}/graph/search", response_model=SemanticSearchResponse)
async def semantic_search(
    world_id: str,
    request: SemanticSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Perform semantic search across world entities.

    Uses embeddings to find entities that semantically match the query.
    """
    from shinkei.agent.graph_rag_service import GraphRAGService

    service = GraphRAGService(db)
    results = await service.semantic_search(
        world_id=world_id,
        query=request.query,
        entity_types=request.entity_types,
        limit=request.limit
    )

    return SemanticSearchResponse(
        query=request.query,
        results=[
            SemanticSearchResultItem(
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                summary=r.semantic_summary,
                relevance_score=round(r.relevance_score, 3),
                importance_score=round(r.importance_score, 3)
            )
            for r in results
        ],
        total=len(results)
    )


# ========================
# TOOLS LISTING
# ========================

class ToolDefinitionItem(BaseModel):
    """Single tool definition."""
    name: str
    description: str
    parameters: dict
    requires_approval: bool
    category: str
    enabled: bool


class ToolListResponse(BaseModel):
    """Response for tool list."""
    tools: List[ToolDefinitionItem]
    total: int
    by_category: dict


@router.get("/tools", response_model=ToolListResponse)
async def list_tools(
    category: Optional[str] = Query(None, pattern="^(read|write|analyze|navigate|graph)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all available tools for the agent.

    Tools are categorized by type (read, write, analyze, navigate, graph).
    Write and graph tools require approval in Ask mode.
    """
    from shinkei.agent.tools.registry import ToolRegistry, ToolCategory

    if category:
        cat_enum = ToolCategory(category)
        tools = ToolRegistry.list_by_category(cat_enum)
    else:
        tools = ToolRegistry.list_enabled()

    # Count by category
    by_category = {}
    for t in ToolRegistry.list_enabled():
        cat_name = t.category.value
        by_category[cat_name] = by_category.get(cat_name, 0) + 1

    return ToolListResponse(
        tools=[
            ToolDefinitionItem(
                name=t.name,
                description=t.description,
                parameters=t.parameters,
                requires_approval=t.requires_approval,
                category=t.category.value,
                enabled=t.enabled
            )
            for t in tools
        ],
        total=len(tools),
        by_category=by_category
    )


# ========================
# RELATED ENTITIES
# ========================

class RelatedEntitiesRequest(BaseModel):
    """Request body for finding related entities."""
    entity_type: str = Field(..., pattern="^(character|location|event|story|beat)$")
    entity_id: str
    depth: int = Field(2, ge=1, le=5)
    relationship_types: Optional[List[str]] = None


@router.post("/worlds/{world_id}/graph/related")
async def find_related_entities(
    world_id: str,
    request: RelatedEntitiesRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Find entities related to a specific entity through graph traversal.

    Returns connected entities and their relationships.
    """
    from shinkei.agent.graph_rag_service import GraphRAGService

    service = GraphRAGService(db)
    result = await service.find_related_entities(
        world_id=world_id,
        entity_type=request.entity_type,
        entity_id=request.entity_id,
        depth=request.depth,
        relationship_types=request.relationship_types
    )

    # Format response
    by_type = {}
    for node in result.nodes:
        if node.entity_type not in by_type:
            by_type[node.entity_type] = []
        by_type[node.entity_type].append({
            "entity_id": node.entity_id,
            "summary": node.semantic_summary,
            "importance": round(node.importance_score, 3)
        })

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
        "source": {"type": request.entity_type, "id": request.entity_id},
        "related_entities": by_type,
        "relationships": edges,
        "total_nodes": len(result.nodes),
        "total_edges": len(result.edges)
    }
