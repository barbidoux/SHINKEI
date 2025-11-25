<script lang="ts">
    import { page } from '$app/stores';
    import { onMount } from 'svelte';
    import { chatStore, sendChatMessage, createConversation, loadConversations, loadConversation, approveAction, deleteConversation } from '$lib/stores/chat';
    import type { AgentPersona, ChatMessage, PendingAction, ToolResult } from '$lib/types';
    import { api } from '$lib/api';
    import { addToast } from '$lib/stores/toast';
    import ChatHeader from './ChatHeader.svelte';
    import ChatMessages from './ChatMessages.svelte';
    import ChatInput from './ChatInput.svelte';
    import ModeSelector from './ModeSelector.svelte';
    import ContextBadges from './ContextBadges.svelte';
    import PersonaManager from './PersonaManager.svelte';
    import WorldCoherenceSettings from './WorldCoherenceSettings.svelte';
    import GraphSyncStatus from './GraphSyncStatus.svelte';

    // Local state
    let personas: AgentPersona[] = [];
    let approvalProcessing = false;
    let showSettings = false;
    let showPersonaManager = false;
    let lastLoadedWorldId: string | null = null;
    let settingsTab: 'provider' | 'coherence' | 'graph' = 'provider';

    // Local mode variable synced with store
    let currentMode = $chatStore.mode;
    $: currentMode = $chatStore.mode;

    // Local provider/model for settings
    let settingsProvider = $chatStore.providerOverride || '';
    let settingsModel = $chatStore.modelOverride || '';

    // Extract world ID from route - only update context if values actually changed
    $: routeWorldId = $page.route.id?.includes('worlds') ? $page.params.id : undefined;
    $: routeStoryId = $page.route.id?.includes('stories') ? $page.params.id : undefined;
    $: routeBeatId = $page.route.id?.includes('beats') ? $page.params.beat_id : undefined;
    $: routeCharacterId = $page.route.id?.includes('characters') ? $page.params.character_id : undefined;
    $: routeLocationId = $page.route.id?.includes('locations') ? $page.params.location_id : undefined;

    // Update context only when route IDs actually change
    $: {
        const currentContext = $chatStore.context;
        if (
            currentContext.worldId !== routeWorldId ||
            currentContext.storyId !== routeStoryId ||
            currentContext.beatId !== routeBeatId ||
            currentContext.characterId !== routeCharacterId ||
            currentContext.locationId !== routeLocationId
        ) {
            chatStore.setContext({
                worldId: routeWorldId,
                storyId: routeStoryId,
                beatId: routeBeatId,
                characterId: routeCharacterId,
                locationId: routeLocationId
            });
        }
    }

    // Load conversations when world context changes - with guard to prevent loops
    $: if ($chatStore.context.worldId && $chatStore.context.worldId !== lastLoadedWorldId) {
        const worldIdToLoad = $chatStore.context.worldId;
        lastLoadedWorldId = worldIdToLoad;
        loadWorldData(worldIdToLoad);
    }

    async function loadWorldData(worldId: string) {
        await Promise.all([
            loadWorldConversations(worldId),
            loadWorldPersonas(worldId)
        ]);
    }

    async function loadWorldConversations(worldId: string) {
        try {
            const conversations = await loadConversations(worldId);
            chatStore.setConversations(conversations);
        } catch (e) {
            console.error('Failed to load conversations:', e);
        }
    }

    async function loadWorldPersonas(worldId: string) {
        try {
            const response = await api.get<{ personas: AgentPersona[] }>(`/agent/worlds/${worldId}/personas`);
            personas = response.personas;
        } catch (e) {
            console.error('Failed to load personas:', e);
            // Use empty array - personas endpoint may not exist yet
            personas = [];
        }
    }

    async function handleNewChat() {
        if (!$chatStore.context.worldId) {
            addToast({ type: 'warning', message: 'Navigate to a world first' });
            return;
        }

        try {
            const conv = await createConversation($chatStore.context.worldId, {
                mode: $chatStore.mode,
                personaId: $chatStore.currentPersonaId || undefined,
                providerOverride: $chatStore.providerOverride || undefined,
                modelOverride: $chatStore.modelOverride || undefined
            });
            chatStore.setConversation(conv.id);
            chatStore.setMessages([]);
            // Reload conversation list
            await loadWorldConversations($chatStore.context.worldId);
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to create conversation' });
        }
    }

    async function handleSelectConversation(event: CustomEvent<string>) {
        const conversationId = event.detail;
        try {
            chatStore.setConversation(conversationId);
            const messages = await loadConversation(conversationId);
            chatStore.setMessages(messages);
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to load conversation' });
        }
    }

    async function handleSendMessage(event: CustomEvent<string>) {
        const message = event.detail;

        if (!$chatStore.context.worldId) {
            addToast({ type: 'warning', message: 'Navigate to a world to chat' });
            return;
        }

        // Create conversation if none exists
        if (!$chatStore.currentConversationId) {
            try {
                const conv = await createConversation($chatStore.context.worldId, {
                    mode: $chatStore.mode,
                    personaId: $chatStore.currentPersonaId || undefined
                });
                chatStore.setConversation(conv.id);
            } catch (e: unknown) {
                const error = e as Error;
                addToast({ type: 'error', message: error.message || 'Failed to create conversation' });
                return;
            }
        }

        // Add user message
        const userMessage: ChatMessage = {
            id: crypto.randomUUID(),
            role: 'user',
            content: message,
            timestamp: new Date()
        };
        chatStore.addMessage(userMessage);

        // Start streaming
        chatStore.setLoading(true);
        chatStore.clearStreaming();
        chatStore.setError(null);

        try {
            await sendChatMessage(
                $chatStore.context.worldId!,
                $chatStore.currentConversationId!,
                message,
                $chatStore.context,
                $chatStore.mode,
                handleChatEvent
            );
        } catch (e: unknown) {
            const error = e as Error;
            chatStore.setError(error.message || 'Failed to send message');
            addToast({ type: 'error', message: error.message || 'Chat error' });

            // On error, add streaming content as message if we have any
            const state = chatStore.getState();
            if (state.streamingContent) {
                const assistantMessage: ChatMessage = {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: state.streamingContent,
                    timestamp: new Date(),
                    thinking: state.streamingThinking || undefined
                };
                chatStore.addMessage(assistantMessage);
                chatStore.clearStreaming();
            }
        } finally {
            chatStore.setLoading(false);
        }
    }

    function handleChatEvent(event: Record<string, unknown>) {
        // Backend sends flat events: {type: "token", content: "..."} not {type, data: {...}}
        const eventType = event.type as string;

        switch (eventType) {
            case 'token':
                chatStore.appendStreamingContent(event.content as string || '');
                break;

            case 'thinking':
                chatStore.appendStreamingThinking(event.content as string || '');
                break;

            case 'tool_use':
                // Tool calls are handled in the complete message
                break;

            case 'tool_result':
                // Tool results are handled in the complete message
                break;

            case 'approval_needed':
                chatStore.setPendingApproval({
                    id: event.message_id as string || crypto.randomUUID(),
                    tool: event.tool as string || '',
                    params: event.params as Record<string, unknown> || {},
                    description: event.message as string
                });
                break;

            case 'complete':
                // Final message from assistant
                const content = event.content as string || $chatStore.streamingContent;
                if (content) {
                    const assistantMessage: ChatMessage = {
                        id: event.message_id as string || crypto.randomUUID(),
                        role: 'assistant',
                        content,
                        timestamp: new Date(),
                        thinking: $chatStore.streamingThinking || undefined,
                        toolCalls: event.tool_calls as ChatMessage['toolCalls'],
                        toolResults: event.results as ToolResult[]
                    };
                    chatStore.addMessage(assistantMessage);
                    chatStore.clearStreaming();
                }
                break;

            case 'error':
                chatStore.setError(event.message as string || 'Unknown error');
                break;
        }
    }

    async function handleApprove() {
        if (!$chatStore.pendingApproval || !$chatStore.currentConversationId) return;

        approvalProcessing = true;
        try {
            const results = await approveAction(
                $chatStore.currentConversationId,
                $chatStore.pendingApproval.id,
                true
            );

            // Add results as tool result message
            if (results.length > 0) {
                const toolMessage: ChatMessage = {
                    id: crypto.randomUUID(),
                    role: 'assistant',
                    content: 'Action completed.',
                    timestamp: new Date(),
                    toolResults: results
                };
                chatStore.addMessage(toolMessage);
            }

            chatStore.setPendingApproval(null);
            addToast({ type: 'success', message: 'Action approved and executed' });
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to process approval' });
        } finally {
            approvalProcessing = false;
        }
    }

    async function handleReject() {
        if (!$chatStore.pendingApproval || !$chatStore.currentConversationId) return;

        approvalProcessing = true;
        try {
            await approveAction(
                $chatStore.currentConversationId,
                $chatStore.pendingApproval.id,
                false
            );

            chatStore.setPendingApproval(null);
            addToast({ type: 'info', message: 'Action rejected' });
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to process rejection' });
        } finally {
            approvalProcessing = false;
        }
    }

    function handleSelectPersona(event: CustomEvent<string | null>) {
        chatStore.setPersona(event.detail);
    }

    async function handleDeleteConversation(event: CustomEvent<string>) {
        const conversationId = event.detail;
        try {
            await deleteConversation(conversationId);

            // If we deleted the current conversation, clear it
            if ($chatStore.currentConversationId === conversationId) {
                chatStore.setConversation(null);
                chatStore.setMessages([]);
            }

            // Reload conversations
            if ($chatStore.context.worldId) {
                await loadWorldConversations($chatStore.context.worldId);
            }

            addToast({ type: 'success', message: 'Conversation deleted' });
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to delete conversation' });
        }
    }

    function handleClose() {
        chatStore.close();
    }

    function handlePersonaCreated(event: CustomEvent<AgentPersona>) {
        personas = [...personas, event.detail];
    }

    function handlePersonaDeleted(event: CustomEvent<string>) {
        personas = personas.filter(p => p.id !== event.detail);
        // If the deleted persona was selected, clear the selection
        if ($chatStore.currentPersonaId === event.detail) {
            chatStore.setPersona(null);
        }
    }
</script>

<div class="h-full flex flex-col bg-white dark:bg-gray-800">
    <!-- Header -->
    <ChatHeader
        currentConversationId={$chatStore.currentConversationId}
        conversations={$chatStore.conversations}
        {personas}
        currentPersonaId={$chatStore.currentPersonaId}
        on:close={handleClose}
        on:newChat={handleNewChat}
        on:selectConversation={handleSelectConversation}
        on:deleteConversation={handleDeleteConversation}
        on:selectPersona={handleSelectPersona}
        on:openSettings={() => showSettings = true}
        on:managePersonas={() => showPersonaManager = true}
    />

    <!-- Context badges -->
    <ContextBadges context={$chatStore.context} />

    <!-- Messages area -->
    <div class="flex-1 min-h-0 relative">
        <ChatMessages
            messages={$chatStore.messages}
            streamingContent={$chatStore.streamingContent}
            streamingThinking={$chatStore.streamingThinking}
            isLoading={$chatStore.isLoading}
            pendingApproval={$chatStore.pendingApproval}
            {approvalProcessing}
            onApprove={handleApprove}
            onReject={handleReject}
        />
    </div>

    <!-- Error display -->
    {#if $chatStore.error}
        <div class="px-3 py-2 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-700">
            <p class="text-xs text-red-600 dark:text-red-400">{$chatStore.error}</p>
        </div>
    {/if}

    <!-- Input area -->
    <div class="flex-shrink-0 border-t border-gray-200 dark:border-gray-700 p-3 space-y-2">
        <!-- Mode selector -->
        <ModeSelector bind:mode={currentMode} on:change={() => chatStore.setMode(currentMode)} />

        <!-- Input -->
        <ChatInput
            on:send={handleSendMessage}
            disabled={$chatStore.isLoading || !!$chatStore.pendingApproval || !$chatStore.context.worldId}
            placeholder={!$chatStore.context.worldId ? 'Navigate to a world to chat...' : 'Ask Story Pilot...'}
        />
    </div>
</div>

<!-- Settings modal with tabs -->
{#if showSettings}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-modal-title"
        tabindex="-1"
        on:click={() => showSettings = false}
        on:keydown={(e) => e.key === 'Escape' && (showSettings = false)}
    >
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <div
            class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-[480px] max-h-[80vh] overflow-hidden flex flex-col"
            role="document"
            on:click|stopPropagation
            on:keydown|stopPropagation
        >
            <!-- Header -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
                <h3 id="settings-modal-title" class="text-lg font-semibold text-gray-900 dark:text-gray-100">Settings</h3>
                <button
                    on:click={() => showSettings = false}
                    class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                    aria-label="Close settings"
                >
                    <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Tabs -->
            <div class="flex border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
                <button
                    on:click={() => settingsTab = 'provider'}
                    class="flex-1 px-4 py-2 text-sm font-medium {settingsTab === 'provider' ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}"
                >
                    Provider
                </button>
                <button
                    on:click={() => settingsTab = 'coherence'}
                    class="flex-1 px-4 py-2 text-sm font-medium {settingsTab === 'coherence' ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}"
                >
                    Coherence
                </button>
                <button
                    on:click={() => settingsTab = 'graph'}
                    class="flex-1 px-4 py-2 text-sm font-medium {settingsTab === 'graph' ? 'text-indigo-600 dark:text-indigo-400 border-b-2 border-indigo-600 dark:border-indigo-400' : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'}"
                >
                    Graph
                </button>
            </div>

            <!-- Tab content -->
            <div class="p-4 overflow-y-auto flex-1">
                {#if settingsTab === 'provider'}
                    <div class="space-y-4">
                        <!-- Provider override -->
                        <div>
                            <label for="settings-provider" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                LLM Provider Override
                            </label>
                            <select
                                id="settings-provider"
                                bind:value={settingsProvider}
                                on:change={() => chatStore.setProvider(settingsProvider || null)}
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                            >
                                <option value="">Use default</option>
                                <option value="openai">OpenAI</option>
                                <option value="anthropic">Anthropic</option>
                                <option value="ollama">Ollama</option>
                            </select>
                            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                Override the default LLM provider for this chat session
                            </p>
                        </div>

                        <!-- Model override -->
                        <div>
                            <label for="settings-model" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Model Override
                            </label>
                            <input
                                id="settings-model"
                                type="text"
                                bind:value={settingsModel}
                                on:change={() => chatStore.setModel(settingsModel || null)}
                                placeholder="e.g., gpt-4o, claude-3-opus"
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                            />
                            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                Override the default model (leave empty for provider default)
                            </p>
                        </div>
                    </div>

                {:else if settingsTab === 'coherence'}
                    {#if $chatStore.context.worldId}
                        <WorldCoherenceSettings worldId={$chatStore.context.worldId} />
                    {:else}
                        <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                            <p>Navigate to a world to configure coherence settings</p>
                        </div>
                    {/if}

                {:else if settingsTab === 'graph'}
                    {#if $chatStore.context.worldId}
                        <GraphSyncStatus worldId={$chatStore.context.worldId} />
                    {:else}
                        <div class="text-center py-8 text-gray-500 dark:text-gray-400">
                            <p>Navigate to a world to view graph status</p>
                        </div>
                    {/if}
                {/if}
            </div>
        </div>
    </div>
{/if}

<!-- Persona Manager modal -->
{#if $chatStore.context.worldId}
    <PersonaManager
        worldId={$chatStore.context.worldId}
        {personas}
        isOpen={showPersonaManager}
        on:close={() => showPersonaManager = false}
        on:personaCreated={handlePersonaCreated}
        on:personaDeleted={handlePersonaDeleted}
    />
{/if}
