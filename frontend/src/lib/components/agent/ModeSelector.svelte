<script lang="ts">
    import type { AgentMode } from '$lib/types';

    export let mode: AgentMode;

    const modes: { value: AgentMode; label: string; icon: string; description: string; color: string }[] = [
        {
            value: 'plan',
            label: 'Plan',
            icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01',
            description: 'AI creates a plan first, you approve before execution',
            color: 'amber'
        },
        {
            value: 'ask',
            label: 'Ask',
            icon: 'M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
            description: 'AI asks for approval before each write action',
            color: 'blue'
        },
        {
            value: 'auto',
            label: 'Auto',
            icon: 'M13 10V3L4 14h7v7l9-11h-7z',
            description: 'AI executes actions automatically',
            color: 'green'
        }
    ];

    function getColorClasses(color: string, isSelected: boolean): string {
        if (!isSelected) {
            return 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600';
        }
        switch (color) {
            case 'amber':
                return 'bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 border-amber-500 dark:border-amber-400';
            case 'blue':
                return 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 border-blue-500 dark:border-blue-400';
            case 'green':
                return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 border-green-500 dark:border-green-400';
            default:
                return 'bg-gray-100 dark:bg-gray-700';
        }
    }
</script>

<div class="flex gap-1">
    {#each modes as m}
        <button
            class="flex-1 px-2 py-1.5 text-xs rounded-md border transition-colors {getColorClasses(m.color, mode === m.value)} {mode === m.value ? 'border-current' : 'border-transparent'}"
            on:click={() => mode = m.value}
            title={m.description}
        >
            <div class="flex items-center justify-center gap-1">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={m.icon} />
                </svg>
                <span class="font-medium">{m.label}</span>
            </div>
        </button>
    {/each}
</div>
