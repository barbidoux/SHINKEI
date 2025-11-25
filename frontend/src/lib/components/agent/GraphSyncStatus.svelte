<script lang="ts">
    import { createEventDispatcher, onMount } from 'svelte';
    import type { GraphSyncStatus } from '$lib/types';
    import { api } from '$lib/api';
    import { addToast } from '$lib/stores/toast';

    export let worldId: string;
    export let status: GraphSyncStatus | null = null;

    const dispatch = createEventDispatcher<{
        updated: GraphSyncStatus;
    }>();

    let loading = false;
    let syncing = false;

    async function loadStatus() {
        loading = true;
        try {
            const response = await api.get<GraphSyncStatus>(`/agent/worlds/${worldId}/graph/status`);
            status = {
                ...response,
                lastFullSync: response.lastFullSync ? new Date(response.lastFullSync as unknown as string) : undefined,
                lastIncrementalSync: response.lastIncrementalSync ? new Date(response.lastIncrementalSync as unknown as string) : undefined
            };
        } catch (e: unknown) {
            const error = e as Error;
            console.error('Failed to load graph status:', error);
        } finally {
            loading = false;
        }
    }

    async function triggerSync(full: boolean = false) {
        syncing = true;
        try {
            const response = await api.post<GraphSyncStatus>(`/agent/worlds/${worldId}/graph/sync?full=${full}`);
            status = {
                ...response,
                lastFullSync: response.lastFullSync ? new Date(response.lastFullSync as unknown as string) : undefined,
                lastIncrementalSync: response.lastIncrementalSync ? new Date(response.lastIncrementalSync as unknown as string) : undefined
            };
            dispatch('updated', status);
            addToast({ type: 'success', message: full ? 'Full graph sync completed' : 'Incremental sync completed' });
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to sync graph' });
        } finally {
            syncing = false;
        }
    }

    async function clearGraph() {
        if (!confirm('Clear all graph data? This will require a full rebuild. Are you sure?')) {
            return;
        }

        syncing = true;
        try {
            await api.delete(`/agent/worlds/${worldId}/graph`);
            await loadStatus();
            addToast({ type: 'info', message: 'Graph data cleared' });
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to clear graph' });
        } finally {
            syncing = false;
        }
    }

    function formatDate(date: Date | undefined): string {
        if (!date) return 'Never';
        return date.toLocaleString();
    }

    // Load status on mount if not provided
    onMount(() => {
        if (worldId && !status) {
            loadStatus();
        }
    });

    $: if (worldId && !status && !loading) {
        loadStatus();
    }
</script>

<div class="space-y-4">
    {#if loading}
        <div class="flex items-center justify-center py-8">
            <svg class="w-6 h-6 animate-spin text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        </div>
    {:else if status}
        <!-- Status Overview -->
        <div class="grid grid-cols-2 gap-4">
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Nodes</p>
                <p class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{status.nodeCount}</p>
            </div>
            <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-3">
                <p class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">Edges</p>
                <p class="text-2xl font-semibold text-gray-900 dark:text-gray-100">{status.edgeCount}</p>
            </div>
        </div>

        <!-- Sync Status -->
        {#if status.syncInProgress}
            <div class="flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <svg class="w-4 h-4 animate-spin text-blue-600 dark:text-blue-400" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-sm text-blue-700 dark:text-blue-300">Sync in progress...</span>
            </div>
        {/if}

        {#if status.lastError}
            <div class="px-3 py-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
                <p class="text-sm text-red-700 dark:text-red-300">
                    <strong>Last Error:</strong> {status.lastError}
                </p>
            </div>
        {/if}

        <!-- Last Sync Times -->
        <div class="space-y-2 text-sm">
            <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">Last Full Sync:</span>
                <span class="text-gray-900 dark:text-gray-100">{formatDate(status.lastFullSync)}</span>
            </div>
            <div class="flex justify-between">
                <span class="text-gray-600 dark:text-gray-400">Last Incremental Sync:</span>
                <span class="text-gray-900 dark:text-gray-100">{formatDate(status.lastIncrementalSync)}</span>
            </div>
        </div>

        <!-- Actions -->
        <div class="space-y-2 pt-2">
            <button
                on:click={() => triggerSync(false)}
                disabled={syncing || status.syncInProgress}
                class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
                {#if syncing}
                    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                {/if}
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Incremental Sync
            </button>

            <button
                on:click={() => triggerSync(true)}
                disabled={syncing || status.syncInProgress}
                class="w-full px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
                {#if syncing}
                    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                {/if}
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Full Rebuild
            </button>

            <button
                on:click={clearGraph}
                disabled={syncing || status.syncInProgress}
                class="w-full px-4 py-2 border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 disabled:opacity-50"
            >
                Clear Graph Data
            </button>
        </div>

        <!-- Info -->
        <p class="text-xs text-gray-500 dark:text-gray-400">
            The knowledge graph stores embeddings for semantic search and entity relationships. Incremental sync updates changed entities only. Full rebuild recreates the entire graph.
        </p>
    {:else}
        <div class="text-center py-4">
            <p class="text-sm text-gray-500 dark:text-gray-400">No graph data available</p>
            <button
                on:click={() => triggerSync(true)}
                disabled={syncing}
                class="mt-2 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
                Build Graph
            </button>
        </div>
    {/if}
</div>
