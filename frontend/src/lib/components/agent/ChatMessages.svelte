<script lang="ts">
    import { afterUpdate, onMount } from 'svelte';
    import type { ChatMessage as ChatMessageType, PendingAction } from '$lib/types';
    import ChatMessage from './ChatMessage.svelte';
    import ApprovalPrompt from './ApprovalPrompt.svelte';

    export let messages: ChatMessageType[];
    export let streamingContent = '';
    export let streamingThinking = '';
    export let isLoading = false;
    export let pendingApproval: PendingAction | null = null;
    export let approvalProcessing = false;
    export let onApprove: () => void = () => {};
    export let onReject: () => void = () => {};

    let containerEl: HTMLDivElement;
    let autoScroll = true;

    // Auto-scroll to bottom when new messages arrive
    afterUpdate(() => {
        if (autoScroll && containerEl) {
            containerEl.scrollTop = containerEl.scrollHeight;
        }
    });

    // Handle scroll to detect if user scrolled up
    function handleScroll() {
        if (containerEl) {
            const { scrollTop, scrollHeight, clientHeight } = containerEl;
            // If user is within 100px of bottom, enable auto-scroll
            autoScroll = scrollHeight - scrollTop - clientHeight < 100;
        }
    }

    // Scroll to bottom button click
    function scrollToBottom() {
        if (containerEl) {
            containerEl.scrollTop = containerEl.scrollHeight;
            autoScroll = true;
        }
    }

    // Check if there's streaming assistant response
    $: hasStreamingResponse = isLoading && (streamingContent || streamingThinking);
</script>

<div
    bind:this={containerEl}
    on:scroll={handleScroll}
    class="h-full overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 dark:scrollbar-thumb-gray-600"
>
    {#if messages.length === 0 && !hasStreamingResponse}
        <!-- Empty state -->
        <div class="h-full flex items-center justify-center p-6">
            <div class="text-center">
                <div class="w-16 h-16 mx-auto mb-4 rounded-full bg-indigo-100 dark:bg-indigo-900/40 flex items-center justify-center">
                    <svg class="w-8 h-8 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                </div>
                <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
                    Story Pilot
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 max-w-xs">
                    Your AI writing assistant. Ask questions about your world, get suggestions, or let me help write your story.
                </p>
            </div>
        </div>
    {:else}
        <!-- Messages list -->
        <div class="divide-y divide-gray-100 dark:divide-gray-700/50">
            {#each messages as message (message.id)}
                <ChatMessage
                    {message}
                    isStreaming={false}
                />
            {/each}

            <!-- Streaming response in progress -->
            {#if hasStreamingResponse}
                <ChatMessage
                    message={{
                        id: 'streaming',
                        role: 'assistant',
                        content: streamingContent,
                        timestamp: new Date(),
                        thinking: streamingThinking || undefined
                    }}
                    isStreaming={true}
                />
            {/if}

            <!-- Loading indicator (no content yet) -->
            {#if isLoading && !streamingContent && !streamingThinking}
                <div class="px-3 py-2">
                    <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                        <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Story Pilot is thinking...
                    </div>
                </div>
            {/if}

            <!-- Pending approval -->
            {#if pendingApproval}
                <div class="px-3 py-2">
                    <ApprovalPrompt
                        action={pendingApproval}
                        isProcessing={approvalProcessing}
                        on:approve={onApprove}
                        on:reject={onReject}
                    />
                </div>
            {/if}
        </div>
    {/if}
</div>

<!-- Scroll to bottom button (shown when not auto-scrolling) -->
{#if !autoScroll && messages.length > 0}
    <button
        on:click={scrollToBottom}
        class="absolute bottom-20 right-4 p-2 rounded-full bg-white dark:bg-gray-700 shadow-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 transition-colors"
        title="Scroll to bottom"
    >
        <svg class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
    </button>
{/if}
