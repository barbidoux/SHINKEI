<script lang="ts">
    import type { VariationFocusOption } from "$lib/types";
    import { PARAM_DESCRIPTIONS, VARIATION_FOCUS_OPTIONS } from "$lib/types";

    export let proposalDiversity: number = 0.5;
    export let variationFocus: VariationFocusOption | null = null;

    // Helper to toggle selection
    function toggleOption<T>(current: T | null, value: T): T | null {
        return current === value ? null : value;
    }
</script>

<div
    class="collaborative-options space-y-4 p-4 bg-purple-50 dark:bg-purple-900/10 rounded-lg border border-purple-200 dark:border-purple-800"
>
    <h4
        class="text-sm font-semibold text-purple-900 dark:text-purple-100 flex items-center gap-2"
    >
        Proposal Variation
    </h4>

    <!-- Proposal Diversity Slider -->
    <div>
        <div class="flex justify-between items-center mb-1">
            <label class="text-sm text-gray-700 dark:text-gray-300">
                Diversity: {(proposalDiversity * 100).toFixed(0)}%
            </label>
            <span
                class="text-xs text-gray-500 cursor-help"
                title={PARAM_DESCRIPTIONS.proposal_diversity}>?</span
            >
        </div>
        <input
            type="range"
            bind:value={proposalDiversity}
            min="0"
            max="1"
            step="0.1"
            class="w-full h-2 bg-purple-200 rounded-lg appearance-none cursor-pointer dark:bg-purple-800"
        />
        <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>Similar</span>
            <span>Very Different</span>
        </div>
    </div>

    <!-- Variation Focus -->
    <div>
        <label class="block text-sm text-gray-700 dark:text-gray-300 mb-2">
            Vary by:
            <span
                class="text-xs text-gray-500 ml-1 cursor-help"
                title={PARAM_DESCRIPTIONS.variation_focus}>?</span
            >
        </label>
        <div class="grid grid-cols-2 gap-2">
            {#each VARIATION_FOCUS_OPTIONS as opt}
                <button
                    type="button"
                    on:click={() =>
                        (variationFocus = toggleOption(variationFocus, opt.value))}
                    class="px-3 py-2 text-xs rounded-md border transition-colors
                        {variationFocus === opt.value
                        ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 text-purple-900 dark:text-purple-100'
                        : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400'}"
                >
                    {opt.emoji} {opt.label}
                </button>
            {/each}
        </div>
    </div>
</div>
