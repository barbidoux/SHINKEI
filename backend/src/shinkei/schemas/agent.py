"""Agent Pydantic schemas for Story Pilot API validation."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


# ========================
# ENUMS
# ========================

class AgentModeEnum(str, Enum):
    """Agent interaction modes."""
    plan = "plan"
    ask = "ask"
    auto = "auto"


class ToolCategoryEnum(str, Enum):
    """Tool categories."""
    read = "read"
    write = "write"
    analyze = "analyze"
    navigate = "navigate"
    graph = "graph"


class TimeConsistencyEnum(str, Enum):
    """Time consistency modes for world coherence."""
    strict = "strict"
    flexible = "flexible"
    non_linear = "non-linear"
    irrelevant = "irrelevant"


class SpatialConsistencyEnum(str, Enum):
    """Spatial consistency modes for world coherence."""
    euclidean = "euclidean"
    flexible = "flexible"
    non_euclidean = "non-euclidean"
    irrelevant = "irrelevant"


class CausalityEnum(str, Enum):
    """Causality modes for world coherence."""
    strict = "strict"
    flexible = "flexible"
    paradox_allowed = "paradox-allowed"


class CharacterKnowledgeEnum(str, Enum):
    """Character knowledge modes for world coherence."""
    strict = "strict"
    flexible = "flexible"


class DeathPermanenceEnum(str, Enum):
    """Death permanence modes for world coherence."""
    permanent = "permanent"
    reversible = "reversible"
    fluid = "fluid"


# ========================
# CHAT SCHEMAS
# ========================

class ChatContext(BaseModel):
    """Context for chat request."""
    world_id: str
    story_id: Optional[str] = None
    beat_id: Optional[str] = None
    character_id: Optional[str] = None
    location_id: Optional[str] = None


class ChatRequest(BaseModel):
    """Request for agent chat."""
    model_config = ConfigDict(extra='forbid')

    message: str = Field(..., min_length=1, max_length=10000)
    context: ChatContext
    conversation_id: Optional[str] = None


class ToolCallSchema(BaseModel):
    """Schema for a tool call."""
    name: str
    params: Dict[str, Any] = Field(default_factory=dict)


class ToolResultSchema(BaseModel):
    """Schema for a tool result."""
    tool: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ChatEventData(BaseModel):
    """Data payload for chat events."""
    content: Optional[str] = None
    message: Optional[str] = None
    tool: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Dict[str, Any]] = None
    results: Optional[List[ToolResultSchema]] = None
    message_id: Optional[str] = None


class ChatEvent(BaseModel):
    """Event emitted during chat processing."""
    type: str = Field(..., pattern="^(token|thinking|tool_use|tool_result|approval_needed|complete|error)$")
    data: ChatEventData


# ========================
# CONVERSATION SCHEMAS
# ========================

class ConversationCreateRequest(BaseModel):
    """Request for creating a conversation."""
    model_config = ConfigDict(extra='forbid')

    title: Optional[str] = Field(None, max_length=200)
    mode: AgentModeEnum = AgentModeEnum.ask
    persona_id: Optional[str] = None
    provider_override: Optional[str] = Field(None, pattern="^(openai|anthropic|ollama)$")
    model_override: Optional[str] = Field(None, max_length=100)


class ConversationMessageSchema(BaseModel):
    """Schema for conversation message."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    reasoning: Optional[str] = None
    tool_calls: Optional[Dict[str, Any]] = None
    tool_results: Optional[Dict[str, Any]] = None
    pending_approval: bool = False
    created_at: datetime


class ConversationSchema(BaseModel):
    """Schema for conversation response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    world_id: str
    user_id: str
    title: str
    mode: str
    persona_id: Optional[str] = None
    provider_override: Optional[str] = None
    model_override: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConversationWithMessagesSchema(ConversationSchema):
    """Schema for conversation with messages."""
    messages: List[ConversationMessageSchema] = []


class ConversationListResponse(BaseModel):
    """Response for conversation list."""
    conversations: List[ConversationSchema]
    total: int
    skip: int
    limit: int


# ========================
# APPROVAL SCHEMAS
# ========================

class ApprovalRequest(BaseModel):
    """Request for approving/rejecting a pending action."""
    model_config = ConfigDict(extra='forbid')

    message_id: str
    approved: bool


class ApprovalResponse(BaseModel):
    """Response for approval action."""
    status: str
    results: Optional[List[ToolResultSchema]] = None
    error: Optional[str] = None


# ========================
# PERSONA SCHEMAS
# ========================

class PersonaTraits(BaseModel):
    """Persona traits schema."""
    personality: Optional[str] = None
    expertise: Optional[List[str]] = None
    communication_style: Optional[str] = None


class GenerationDefaults(BaseModel):
    """Default generation settings for persona."""
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=100, le=16000)
    top_p: Optional[float] = Field(None, ge=0.0, le=1.0)
    frequency_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)
    presence_penalty: Optional[float] = Field(None, ge=-2.0, le=2.0)


class PersonaCreateRequest(BaseModel):
    """Request for creating a persona."""
    model_config = ConfigDict(extra='forbid')

    name: str = Field(..., min_length=1, max_length=200)
    system_prompt: str = Field(..., min_length=10, max_length=10000)
    traits: Optional[PersonaTraits] = None
    generation_defaults: Optional[GenerationDefaults] = None


class PersonaUpdateRequest(BaseModel):
    """Request for updating a persona."""
    model_config = ConfigDict(extra='forbid')

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    system_prompt: Optional[str] = Field(None, min_length=10, max_length=10000)
    traits: Optional[PersonaTraits] = None
    generation_defaults: Optional[GenerationDefaults] = None
    is_active: Optional[bool] = None


class PersonaSchema(BaseModel):
    """Schema for persona response."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    world_id: Optional[str] = None
    name: str
    system_prompt: str
    traits: Dict[str, Any] = Field(default_factory=dict)
    generation_defaults: Dict[str, Any] = Field(default_factory=dict)
    is_builtin: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PersonaListResponse(BaseModel):
    """Response for persona list."""
    personas: List[PersonaSchema]
    total: int


# ========================
# COHERENCE SETTINGS SCHEMAS
# ========================

class CoherenceSettingsCreateRequest(BaseModel):
    """Request for creating/updating coherence settings."""
    model_config = ConfigDict(extra='forbid')

    time_consistency: TimeConsistencyEnum = TimeConsistencyEnum.flexible
    spatial_consistency: SpatialConsistencyEnum = SpatialConsistencyEnum.euclidean
    causality: CausalityEnum = CausalityEnum.flexible
    character_knowledge: CharacterKnowledgeEnum = CharacterKnowledgeEnum.strict
    death_permanence: DeathPermanenceEnum = DeathPermanenceEnum.permanent
    custom_rules: Optional[List[str]] = None


class CoherenceSettingsUpdateRequest(BaseModel):
    """Request for updating coherence settings."""
    model_config = ConfigDict(extra='forbid')

    time_consistency: Optional[TimeConsistencyEnum] = None
    spatial_consistency: Optional[SpatialConsistencyEnum] = None
    causality: Optional[CausalityEnum] = None
    character_knowledge: Optional[CharacterKnowledgeEnum] = None
    death_permanence: Optional[DeathPermanenceEnum] = None
    custom_rules: Optional[List[str]] = None


class CoherenceSettingsSchema(BaseModel):
    """Schema for coherence settings response."""
    model_config = ConfigDict(from_attributes=True)

    world_id: str
    time_consistency: str
    spatial_consistency: str
    causality: str
    character_knowledge: str
    death_permanence: str
    custom_rules: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ========================
# GRAPH STATUS SCHEMAS
# ========================

class GraphStatusSchema(BaseModel):
    """Schema for graph status response."""
    world_id: str
    node_count: int
    edge_count: int
    last_full_sync: Optional[datetime] = None
    last_incremental_sync: Optional[datetime] = None
    sync_in_progress: bool = False
    last_error: Optional[str] = None


class GraphBuildRequest(BaseModel):
    """Request for building graph."""
    model_config = ConfigDict(extra='forbid')

    full_rebuild: bool = False


class GraphBuildResponse(BaseModel):
    """Response for graph build."""
    status: str
    nodes_created: Optional[int] = None
    nodes_updated: Optional[int] = None
    edges_created: Optional[int] = None
    errors: Optional[List[str]] = None
    error: Optional[str] = None
    reason: Optional[str] = None


# ========================
# TOOL SCHEMAS
# ========================

class ToolParameterSchema(BaseModel):
    """Schema for tool parameter definition."""
    type: str
    description: Optional[str] = None
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    items: Optional[Dict[str, Any]] = None


class ToolDefinitionSchema(BaseModel):
    """Schema for tool definition."""
    name: str
    description: str
    parameters: Dict[str, Any]
    requires_approval: bool = False
    category: ToolCategoryEnum = ToolCategoryEnum.read
    enabled: bool = True


class ToolListResponse(BaseModel):
    """Response for tool list."""
    tools: List[ToolDefinitionSchema]
    total: int
    by_category: Dict[str, int]


# ========================
# SEMANTIC SEARCH SCHEMAS
# ========================

class SemanticSearchRequest(BaseModel):
    """Request for semantic search."""
    model_config = ConfigDict(extra='forbid')

    query: str = Field(..., min_length=1, max_length=1000)
    entity_types: Optional[List[str]] = None
    limit: int = Field(10, ge=1, le=100)
    min_score: float = Field(0.5, ge=0.0, le=1.0)


class SemanticSearchResultSchema(BaseModel):
    """Schema for semantic search result."""
    node_id: str
    entity_type: str
    entity_id: str
    semantic_summary: Optional[str] = None
    importance_score: float
    relevance_score: float


class SemanticSearchResponse(BaseModel):
    """Response for semantic search."""
    query: str
    results: List[SemanticSearchResultSchema]
    total: int


# ========================
# RELATED ENTITIES SCHEMAS
# ========================

class RelatedEntitiesRequest(BaseModel):
    """Request for finding related entities."""
    model_config = ConfigDict(extra='forbid')

    entity_type: str = Field(..., pattern="^(character|location|event|story|beat)$")
    entity_id: str
    depth: int = Field(2, ge=1, le=5)
    relationship_types: Optional[List[str]] = None


class EntitySummarySchema(BaseModel):
    """Schema for entity summary in graph results."""
    entity_id: str
    summary: Optional[str] = None
    importance: float


class RelationshipSchema(BaseModel):
    """Schema for relationship in graph results."""
    source: str
    target: str
    type: str
    strength: float


class RelatedEntitiesResponse(BaseModel):
    """Response for related entities."""
    source: Dict[str, str]
    related_entities: Dict[str, List[EntitySummarySchema]]
    relationships: List[RelationshipSchema]
    total_nodes: int
    total_edges: int
