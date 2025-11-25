<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { ConversationSummary, AgentPersona } from '$lib/types';

    export let currentConversationId: string | null;
    export let conversations: ConversationSummary[] = [];
    export let personas: AgentPersona[] = [];
    export let currentPersonaId: string | null = null;

    const dispatch = createEventDispatcher<{
        close: void;
        newChat: void;
        selectConversation: string;
        deleteConversation: string;
        selectPersona: string | null;
        openSettings: void;
        managePersonas: void;
    }>();

    function handleDeleteConversation(e: Event, convId: string) {
        e.stopPropagation();
        if (confirm('Delete this conversation? This cannot be undone.')) {
            dispatch('deleteConversation', convId);
        }
    }

    let showConversationList = false;
    let showPersonaSelector = false;

    // Get current persona name
    $: currentPersona = currentPersonaId
        ? personas.find(p => p.id === currentPersonaId)
        : null;

    // Format date for conversation list
    function formatDate(date: Date): string {
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));

        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        return date.toLocaleDateString();
    }
</script>

<div class="flex-shrink-0 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
    <!-- Main header row -->
    <div class="flex items-center gap-2 px-3 py-2">
        <!-- Logo/Title -->
        <div class="flex items-center gap-2 flex-1 min-w-0">
            <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
            </div>
            <div class="flex-1 min-w-0">
                <h2 class="text-sm font-semibold text-gray-900 dark:text-gray-100 truncate">
                    Story Pilot
                </h2>
                {#if currentPersona}
                    <p class="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {currentPersona.name}
                    </p>
                {/if}
            </div>
        </div>

        <!-- Action buttons -->
        <div class="flex items-center gap-1">
            <!-- New chat button -->
            <button
                on:click={() => dispatch('newChat')}
                class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
                title="New conversation"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
            </button>

            <!-- Conversation history -->
            <div class="relative">
                <button
                    on:click={() => { showConversationList = !showConversationList; showPersonaSelector = false; }}
                    class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 {showConversationList ? 'bg-gray-100 dark:bg-gray-700' : ''}"
                    title="Conversation history"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                </button>

                {#if showConversationList}
                    <div class="absolute right-0 top-full mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg z-10 max-h-80 overflow-y-auto">
                        <div class="p-2 border-b border-gray-100 dark:border-gray-700">
                            <h3 class="text-xs font-medium text-gray-500 dark:text-gray-400">Recent Conversations</h3>
                        </div>
                        {#if conversations.length === 0}
                            <div class="p-3 text-xs text-gray-500 dark:text-gray-400 text-center">
                                No conversations yet
                            </div>
                        {:else}
                            {#each conversations as conv}
                                <div class="flex items-center hover:bg-gray-50 dark:hover:bg-gray-700 {conv.id === currentConversationId ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''}">
                                    <button
                                        on:click={() => { dispatch('selectConversation', conv.id); showConversationList = false; }}
                                        class="flex-1 px-3 py-2 text-left"
                                    >
                                        <p class="text-sm text-gray-900 dark:text-gray-100 truncate">{conv.title}</p>
                                        <p class="text-xs text-gray-500 dark:text-gray-400">
                                            {formatDate(conv.updatedAt)} · {conv.messageCount} messages
                                        </p>
                                    </button>
                                    <button
                                        on:click={(e) => handleDeleteConversation(e, conv.id)}
                                        class="p-2 text-gray-400 hover:text-red-500 flex-shrink-0"
                                        title="Delete conversation"
                                    >
                                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                        </svg>
                                    </button>
                                </div>
                            {/each}
                        {/if}
                    </div>
                {/if}
            </div>

            <!-- Persona selector -->
            <div class="relative">
                <button
                    on:click={() => { showPersonaSelector = !showPersonaSelector; showConversationList = false; }}
                    class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 {showPersonaSelector ? 'bg-gray-100 dark:bg-gray-700' : ''}"
                    title="Select persona"
                >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                </button>

                {#if showPersonaSelector}
                    <div class="absolute right-0 top-full mt-1 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg z-10 max-h-80 overflow-y-auto">
                        <div class="p-2 border-b border-gray-100 dark:border-gray-700 flex items-center justify-between">
                            <h3 class="text-xs font-medium text-gray-500 dark:text-gray-400">Select Persona</h3>
                            <button
                                on:click={() => { dispatch('managePersonas'); showPersonaSelector = false; }}
                                class="text-xs text-indigo-600 dark:text-indigo-400 hover:underline"
                            >
                                Manage
                            </button>
                        </div>
                        <!-- Default (no persona) -->
                        <button
                            on:click={() => { dispatch('selectPersona', null); showPersonaSelector = false; }}
                            class="w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 {!currentPersonaId ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''}"
                        >
                            <p class="text-sm text-gray-900 dark:text-gray-100">Default Assistant</p>
                            <p class="text-xs text-gray-500 dark:text-gray-400">Balanced general-purpose helper</p>
                        </button>
                        {#each personas as persona}
                            <button
                                on:click={() => { dispatch('selectPersona', persona.id); showPersonaSelector = false; }}
                                class="w-full px-3 py-2 text-left hover:bg-gray-50 dark:hover:bg-gray-700 {persona.id === currentPersonaId ? 'bg-indigo-50 dark:bg-indigo-900/20' : ''}"
                            >
                                <div class="flex items-center gap-2">
                                    <p class="text-sm text-gray-900 dark:text-gray-100">{persona.name}</p>
                                    {#if persona.isBuiltin}
                                        <span class="text-[10px] px-1 py-0.5 bg-gray-100 dark:bg-gray-600 text-gray-500 dark:text-gray-400 rounded">Built-in</span>
                                    {/if}
                                </div>
                                {#if persona.description}
                                    <p class="text-xs text-gray-500 dark:text-gray-400 truncate">{persona.description}</p>
                                {/if}
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>

            <!-- Settings -->
            <button
                on:click={() => dispatch('openSettings')}
                class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
                title="Chat settings"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
            </button>

            <!-- Close button -->
            <button
                on:click={() => dispatch('close')}
                class="p-1.5 rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
                title="Close panel"
            >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
                </svg>
            </button>
        </div>
    </div>
</div>

<!-- Click outside to close dropdowns -->
<svelte:window on:click={(e) => {
    const target = e.target as HTMLElement;
    if (!target.closest('.relative')) {
        showConversationList = false;
        showPersonaSelector = false;
    }
}} />
