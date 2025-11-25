<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { PendingAction } from '$lib/types';

    export let action: PendingAction;
    export let isProcessing = false;

    const dispatch = createEventDispatcher<{
        approve: void;
        reject: void;
    }>();

    // Human-readable action labels
    const actionLabels: Record<string, string> = {
        create_beat: 'Create new story beat',
        update_beat: 'Update story beat',
        delete_beat: 'Delete story beat',
        create_character: 'Create new character',
        update_character: 'Update character',
        delete_character: 'Delete character',
        create_location: 'Create new location',
        update_location: 'Update location',
        delete_location: 'Delete location',
        create_event: 'Create world event',
        update_event: 'Update world event',
        delete_event: 'Delete world event',
        create_relationship: 'Create character relationship',
        update_relationship: 'Update relationship',
        delete_relationship: 'Delete relationship',
        build_world_graph: 'Build/update world knowledge graph',
        update_story: 'Update story details',
        create_story: 'Create new story'
    };

    // Action category colors
    function getActionColor(tool: string): string {
        if (tool.startsWith('create_')) return 'green';
        if (tool.startsWith('update_')) return 'blue';
        if (tool.startsWith('delete_')) return 'red';
        if (tool.includes('graph') || tool.includes('build')) return 'purple';
        return 'amber';
    }

    $: label = actionLabels[action.tool] || action.tool.replace(/_/g, ' ');
    $: color = getActionColor(action.tool);
</script>

<div class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/50 rounded-lg p-3 my-2">
    <!-- Header -->
    <div class="flex items-center gap-2 mb-2">
        <span class="flex-shrink-0">
            <svg class="w-5 h-5 text-amber-600 dark:text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
        </span>
        <span class="font-medium text-amber-800 dark:text-amber-200">
            Approval Required
        </span>
    </div>

    <!-- Action description -->
    <div class="mb-3">
        <p class="text-sm text-gray-700 dark:text-gray-300">
            The AI wants to: <strong class="
                {color === 'green' ? 'text-green-700 dark:text-green-400' : ''}
                {color === 'blue' ? 'text-blue-700 dark:text-blue-400' : ''}
                {color === 'red' ? 'text-red-700 dark:text-red-400' : ''}
                {color === 'purple' ? 'text-purple-700 dark:text-purple-400' : ''}
                {color === 'amber' ? 'text-amber-700 dark:text-amber-400' : ''}
            ">{label}</strong>
        </p>
        {#if action.description}
            <p class="text-xs text-gray-600 dark:text-gray-400 mt-1">{action.description}</p>
        {/if}
    </div>

    <!-- Parameters preview -->
    <div class="mb-3">
        <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Details</h4>
        <pre class="text-xs bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-600 p-2 rounded overflow-auto max-h-32 font-mono text-gray-700 dark:text-gray-300">{JSON.stringify(action.params, null, 2)}</pre>
    </div>

    <!-- Action buttons -->
    <div class="flex gap-2">
        <button
            class="flex-1 px-3 py-1.5 bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white rounded text-sm font-medium transition-colors flex items-center justify-center gap-1"
            on:click={() => dispatch('approve')}
            disabled={isProcessing}
        >
            {#if isProcessing}
                <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
            {:else}
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                Approve
            {/if}
        </button>
        <button
            class="flex-1 px-3 py-1.5 bg-red-600 hover:bg-red-700 disabled:bg-red-400 text-white rounded text-sm font-medium transition-colors flex items-center justify-center gap-1"
            on:click={() => dispatch('reject')}
            disabled={isProcessing}
        >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Reject
        </button>
    </div>
</div>
