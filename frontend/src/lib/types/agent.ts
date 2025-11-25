/**
 * TypeScript types for the Story Pilot AI Chat Assistant
 */

// Agent interaction modes
export type AgentMode = 'plan' | 'ask' | 'auto';

// Tool categories
export type ToolCategory = 'read' | 'write' | 'analyze' | 'navigate' | 'graph';

// Chat event types from SSE stream
export type ChatEventType = 'token' | 'thinking' | 'tool_use' | 'tool_result' | 'approval_needed' | 'complete' | 'error';

// Tool call representation
export interface ToolCall {
    id: string;
    name: string;
    params: Record<string, unknown>;
}

// Tool result representation
export interface ToolResult {
    tool: string;
    result?: Record<string, unknown>;
    error?: string;
}

// Pending action requiring approval (Ask mode)
export interface PendingAction {
    id: string;
    tool: string;
    params: Record<string, unknown>;
    description?: string;
}

// Chat message
export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string;
    timestamp: Date;
    toolCalls?: ToolCall[];
    toolResults?: ToolResult[];
    pendingApproval?: PendingAction;
    thinking?: string;
    isStreaming?: boolean;
}

// Conversation summary for list view
export interface ConversationSummary {
    id: string;
    title: string;
    mode: AgentMode;
    personaId?: string;
    personaName?: string;
    updatedAt: Date;
    messageCount: number;
}

// Full conversation with messages
export interface Conversation {
    id: string;
    worldId: string;
    userId: string;
    title: string;
    mode: AgentMode;
    personaId?: string;
    providerOverride?: string;
    modelOverride?: string;
    createdAt: Date;
    updatedAt: Date;
    messages: ChatMessage[];
}

// Chat context from current route/location
export interface ChatContext {
    worldId?: string;
    storyId?: string;
    beatId?: string;
    characterId?: string;
    locationId?: string;
}

// Chat request to API
export interface ChatRequest {
    message: string;
    context: ChatContext;
    conversationId?: string;
}

// Chat event from SSE stream
export interface ChatEvent {
    type: ChatEventType;
    data: {
        content?: string;
        message?: string;
        tool?: string;
        params?: Record<string, unknown>;
        result?: Record<string, unknown>;
        results?: ToolResult[];
        messageId?: string;
    };
}

// Create conversation request
export interface CreateConversationRequest {
    title?: string;
    mode?: AgentMode;
    personaId?: string;
    providerOverride?: string;
    modelOverride?: string;
}

// Approval request
export interface ApprovalRequest {
    messageId: string;
    approved: boolean;
}

// Approval response
export interface ApprovalResponse {
    status: string;
    results?: ToolResult[];
    error?: string;
}

// Agent persona
export interface AgentPersona {
    id: string;
    worldId?: string;
    name: string;
    description?: string;
    systemPrompt: string;
    traits: PersonaTraits;
    generationDefaults: GenerationDefaults;
    isBuiltin: boolean;
    isActive: boolean;
    createdAt?: Date;
    updatedAt?: Date;
}

// Persona traits
export interface PersonaTraits {
    personality?: string;
    expertise?: string[];
    communicationStyle?: string;
    strictness?: 'strict' | 'moderate' | 'lenient';
    focusAreas?: string[];
}

// Generation defaults for personas
export interface GenerationDefaults {
    temperature?: number;
    maxTokens?: number;
    topP?: number;
    frequencyPenalty?: number;
    presencePenalty?: number;
}

// Coherence settings for world
export interface CoherenceSettings {
    worldId: string;
    timeConsistency: 'strict' | 'flexible' | 'non-linear' | 'irrelevant';
    spatialConsistency: 'euclidean' | 'flexible' | 'non-euclidean' | 'irrelevant';
    causality: 'strict' | 'flexible' | 'paradox-allowed';
    characterKnowledge: 'strict' | 'flexible';
    deathPermanence: 'permanent' | 'reversible' | 'fluid';
    customRules?: string[];
}

// GraphRAG sync status
export interface GraphSyncStatus {
    worldId: string;
    nodeCount: number;
    edgeCount: number;
    lastFullSync?: Date;
    lastIncrementalSync?: Date;
    syncInProgress: boolean;
    lastError?: string;
}

// Tool definition from API
export interface ToolDefinition {
    name: string;
    description: string;
    parameters: Record<string, unknown>;
    requiresApproval: boolean;
    category: ToolCategory;
    enabled: boolean;
}

// Semantic search result
export interface SemanticSearchResult {
    entityType: string;
    entityId: string;
    summary?: string;
    relevanceScore: number;
    importanceScore: number;
}

// Chat store state
export interface ChatState {
    isOpen: boolean;
    currentConversationId: string | null;
    conversations: ConversationSummary[];
    messages: ChatMessage[];
    isLoading: boolean;
    streamingContent: string;
    streamingThinking: string;
    mode: AgentMode;
    currentPersonaId: string | null;
    providerOverride: string | null;
    modelOverride: string | null;
    pendingApproval: PendingAction | null;
    context: ChatContext;
    error: string | null;
}
