<script lang="ts">
    import type { ToolCall, ToolResult } from '$lib/types';

    export let toolCall: ToolCall;
    export let result: ToolResult | undefined = undefined;
    export let isExecuting = false;

    let expanded = false;

    // Tool category icons
    const categoryIcons: Record<string, string> = {
        read: 'M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z',
        write: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z',
        analyze: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
        graph: 'M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1',
        navigate: 'M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7'
    };

    // Determine tool category from name
    function getToolCategory(name: string): string {
        if (name.startsWith('get_') || name.startsWith('list_') || name.startsWith('search_')) return 'read';
        if (name.startsWith('create_') || name.startsWith('update_') || name.startsWith('delete_')) return 'write';
        if (name.startsWith('check_') || name.startsWith('analyze_') || name.startsWith('validate_')) return 'analyze';
        if (name.includes('graph') || name.includes('semantic') || name.includes('related')) return 'graph';
        return 'read';
    }

    $: category = getToolCategory(toolCall.name);
    $: icon = categoryIcons[category] || categoryIcons.read;
</script>

<div class="rounded-lg border border-gray-200 dark:border-gray-600 overflow-hidden my-2">
    <!-- Header -->
    <button
        class="w-full flex items-center gap-2 px-3 py-2 bg-gray-50 dark:bg-gray-700/50 text-left hover:bg-gray-100 dark:hover:bg-gray-700"
        on:click={() => expanded = !expanded}
    >
        <!-- Tool icon -->
        <div class="flex-shrink-0 w-6 h-6 rounded bg-gray-200 dark:bg-gray-600 flex items-center justify-center">
            <svg class="w-4 h-4 text-gray-600 dark:text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={icon} />
            </svg>
        </div>

        <!-- Tool name -->
        <span class="flex-1 font-mono text-sm text-gray-800 dark:text-gray-200 truncate">
            {toolCall.name}
        </span>

        <!-- Status indicator -->
        {#if isExecuting}
            <span class="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400">
                <svg class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Running...
            </span>
        {:else if result?.error}
            <span class="flex items-center gap-1 text-xs text-red-600 dark:text-red-400">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
                Failed
            </span>
        {:else if result}
            <span class="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                Done
            </span>
        {/if}

        <!-- Expand icon -->
        <svg
            class="w-4 h-4 text-gray-400 transition-transform {expanded ? 'rotate-180' : ''}"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
        >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
    </button>

    <!-- Expanded content -->
    {#if expanded}
        <div class="border-t border-gray-200 dark:border-gray-600">
            <!-- Parameters -->
            <div class="p-3">
                <h4 class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Parameters</h4>
                <pre class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-32 font-mono text-gray-700 dark:text-gray-300">{JSON.stringify(toolCall.params, null, 2)}</pre>
            </div>

            <!-- Result -->
            {#if result}
                <div class="p-3 border-t border-gray-200 dark:border-gray-600">
                    <h4 class="text-xs font-medium {result.error ? 'text-red-500 dark:text-red-400' : 'text-gray-500 dark:text-gray-400'} mb-1">
                        {result.error ? 'Error' : 'Result'}
                    </h4>
                    {#if result.error}
                        <p class="text-xs text-red-600 dark:text-red-400">{result.error}</p>
                    {:else}
                        <pre class="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded overflow-auto max-h-32 font-mono text-gray-700 dark:text-gray-300">{JSON.stringify(result.result, null, 2)}</pre>
                    {/if}
                </div>
            {/if}
        </div>
    {/if}
</div>
