/**
 * Story Pilot Chat Store
 * Manages the state of the AI chat panel
 */
import { writable, get } from 'svelte/store';
import { browser } from '$app/environment';
import type {
    ChatState,
    ChatMessage,
    ChatContext,
    AgentMode,
    ConversationSummary,
    PendingAction,
    ToolResult
} from '$lib/types';
import { auth } from './auth';

const initialState: ChatState = {
    isOpen: false,
    currentConversationId: null,
    conversations: [],
    messages: [],
    isLoading: false,
    streamingContent: '',
    streamingThinking: '',
    mode: 'ask',
    currentPersonaId: null,
    providerOverride: null,
    modelOverride: null,
    pendingApproval: null,
    context: {},
    error: null
};

// Load persisted state from localStorage
function getPersistedState(): Partial<ChatState> {
    if (browser) {
        const stored = localStorage.getItem('chat-state');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                return {
                    isOpen: parsed.isOpen ?? false,
                    mode: parsed.mode ?? 'ask',
                    currentPersonaId: parsed.currentPersonaId ?? null,
                    providerOverride: parsed.providerOverride ?? null,
                    modelOverride: parsed.modelOverride ?? null
                };
            } catch (e) {
                console.error('Failed to parse chat state', e);
            }
        }
    }
    return {};
}

function createChatStore() {
    const persistedState = getPersistedState();
    const { subscribe, set, update } = writable<ChatState>({
        ...initialState,
        ...persistedState
    });

    // Persist certain state changes to localStorage
    function persist(state: ChatState) {
        if (browser) {
            localStorage.setItem('chat-state', JSON.stringify({
                isOpen: state.isOpen,
                mode: state.mode,
                currentPersonaId: state.currentPersonaId,
                providerOverride: state.providerOverride,
                modelOverride: state.modelOverride
            }));
        }
    }

    return {
        subscribe,

        // Toggle panel open/closed
        toggle: () => update(s => {
            const newState = { ...s, isOpen: !s.isOpen };
            persist(newState);
            return newState;
        }),

        // Open panel
        open: () => update(s => {
            const newState = { ...s, isOpen: true };
            persist(newState);
            return newState;
        }),

        // Close panel
        close: () => update(s => {
            const newState = { ...s, isOpen: false };
            persist(newState);
            return newState;
        }),

        // Set agent mode (plan/ask/auto)
        setMode: (mode: AgentMode) => update(s => {
            const newState = { ...s, mode };
            persist(newState);
            return newState;
        }),

        // Update context from current route
        setContext: (context: ChatContext) => update(s => ({
            ...s,
            context
        })),

        // Set current conversation
        setConversation: (id: string | null) => update(s => ({
            ...s,
            currentConversationId: id,
            messages: [],
            pendingApproval: null,
            error: null
        })),

        // Set conversations list
        setConversations: (conversations: ConversationSummary[]) => update(s => ({
            ...s,
            conversations
        })),

        // Add a new message
        addMessage: (message: ChatMessage) => update(s => ({
            ...s,
            messages: [...s.messages, message]
        })),

        // Update the last message (for streaming)
        updateLastMessage: (updates: Partial<ChatMessage>) => update(s => {
            if (s.messages.length === 0) return s;
            const messages = [...s.messages];
            messages[messages.length - 1] = {
                ...messages[messages.length - 1],
                ...updates
            };
            return { ...s, messages };
        }),

        // Set messages (when loading conversation)
        setMessages: (messages: ChatMessage[]) => update(s => ({
            ...s,
            messages
        })),

        // Update streaming content
        updateStreamingContent: (content: string) => update(s => ({
            ...s,
            streamingContent: content
        })),

        // Append to streaming content
        appendStreamingContent: (chunk: string) => update(s => ({
            ...s,
            streamingContent: s.streamingContent + chunk
        })),

        // Update streaming thinking
        updateStreamingThinking: (thinking: string) => update(s => ({
            ...s,
            streamingThinking: thinking
        })),

        // Append to streaming thinking
        appendStreamingThinking: (chunk: string) => update(s => ({
            ...s,
            streamingThinking: s.streamingThinking + chunk
        })),

        // Clear streaming state
        clearStreaming: () => update(s => ({
            ...s,
            streamingContent: '',
            streamingThinking: ''
        })),

        // Set loading state
        setLoading: (isLoading: boolean) => update(s => ({
            ...s,
            isLoading
        })),

        // Set pending approval
        setPendingApproval: (approval: PendingAction | null) => update(s => ({
            ...s,
            pendingApproval: approval
        })),

        // Set error
        setError: (error: string | null) => update(s => ({
            ...s,
            error
        })),

        // Set persona
        setPersona: (personaId: string | null) => update(s => {
            const newState = { ...s, currentPersonaId: personaId };
            persist(newState);
            return newState;
        }),

        // Set provider override
        setProvider: (provider: string | null) => update(s => {
            const newState = { ...s, providerOverride: provider };
            persist(newState);
            return newState;
        }),

        // Set model override
        setModel: (model: string | null) => update(s => {
            const newState = { ...s, modelOverride: model };
            persist(newState);
            return newState;
        }),

        // Reset to initial state
        reset: () => {
            set(initialState);
            if (browser) {
                localStorage.removeItem('chat-state');
            }
        },

        // Get current state value
        getState: () => get({ subscribe })
    };
}

export const chatStore = createChatStore();

// API helper functions
const BASE_URL = browser ? (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') : '';

export async function sendChatMessage(
    worldId: string,
    conversationId: string,
    message: string,
    context: ChatContext,
    mode: AgentMode,
    onEvent: (event: Record<string, unknown>) => void
): Promise<void> {
    const token = get(auth).token;
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(
        `${BASE_URL}/api/v1/agent/worlds/${worldId}/conversations/${conversationId}/chat/stream`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message,
                context,
                mode
            })
        }
    );

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Chat request failed');
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
        throw new Error('Response body is not readable');
    }

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    try {
                        const event = JSON.parse(data);
                        onEvent(event);
                    } catch (parseError) {
                        console.error('Failed to parse SSE event:', parseError);
                    }
                }
            }
        }
    } finally {
        reader.releaseLock();
    }
}

export async function createConversation(
    worldId: string,
    options: {
        title?: string;
        mode?: AgentMode;
        personaId?: string;
        providerOverride?: string;
        modelOverride?: string;
    } = {}
): Promise<{id: string; title: string}> {
    const token = get(auth).token;
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(
        `${BASE_URL}/api/v1/agent/worlds/${worldId}/conversations`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                title: options.title,
                mode: options.mode ?? 'ask',
                persona_id: options.personaId,
                provider_override: options.providerOverride,
                model_override: options.modelOverride
            })
        }
    );

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create conversation');
    }

    return response.json();
}

export async function loadConversations(worldId: string): Promise<ConversationSummary[]> {
    const token = get(auth).token;
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(
        `${BASE_URL}/api/v1/agent/worlds/${worldId}/conversations`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to load conversations');
    }

    const data = await response.json();
    return data.conversations.map((c: Record<string, unknown>) => ({
        id: c.id,
        title: c.title,
        mode: c.mode,
        personaId: c.persona_id,
        updatedAt: new Date(c.updated_at as string),
        messageCount: c.message_count ?? 0
    }));
}

export async function loadConversation(conversationId: string): Promise<ChatMessage[]> {
    const token = get(auth).token;
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(
        `${BASE_URL}/api/v1/agent/conversations/${conversationId}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to load conversation');
    }

    const data = await response.json();
    return data.messages.map((m: Record<string, unknown>) => ({
        id: m.id,
        role: m.role,
        content: m.content,
        timestamp: new Date(m.created_at as string),
        toolCalls: m.tool_calls,
        toolResults: m.tool_results,
        pendingApproval: m.pending_approval ? {
            id: m.id,
            tool: (m.tool_calls as Record<string, unknown>)?.name ?? '',
            params: (m.tool_calls as Record<string, unknown>)?.params ?? {}
        } : undefined,
        thinking: m.reasoning
    }));
}

export async function approveAction(
    conversationId: string,
    messageId: string,
    approved: boolean
): Promise<ToolResult[]> {
    const token = get(auth).token;
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(
        `${BASE_URL}/api/v1/agent/conversations/${conversationId}/approve`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message_id: messageId,
                approved
            })
        }
    );

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to process approval');
    }

    // Handle SSE response from backend
    const results: ToolResult[] = [];
    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
        throw new Error('Response body is not readable');
    }

    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const data = line.slice(6);
                    try {
                        const event = JSON.parse(data);
                        // Collect tool results
                        if (event.type === 'tool_result' && event.result) {
                            results.push(event.result);
                        }
                        // Handle errors
                        if (event.type === 'error') {
                            throw new Error(event.message || event.error || 'Approval action failed');
                        }
                    } catch (parseError) {
                        // Re-throw if it's an Error we created (not a JSON parse error)
                        if (parseError instanceof Error && parseError.message !== 'Unexpected token') {
                            const errMsg = parseError.message;
                            if (!errMsg.includes('JSON') && !errMsg.includes('Unexpected')) {
                                throw parseError;
                            }
                        }
                        // Skip invalid JSON lines (like empty lines)
                        if (data.trim()) {
                            console.warn('Failed to parse SSE event:', parseError);
                        }
                    }
                }
            }
        }
    } finally {
        reader.releaseLock();
    }

    return results;
}

export async function deleteConversation(conversationId: string): Promise<void> {
    const token = get(auth).token;
    if (!token) {
        throw new Error('Not authenticated');
    }

    const response = await fetch(
        `${BASE_URL}/api/v1/agent/conversations/${conversationId}`,
        {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to delete conversation');
    }
}
