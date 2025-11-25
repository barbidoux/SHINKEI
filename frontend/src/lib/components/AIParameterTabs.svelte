<script lang="ts">
    import type {
        LengthPreset,
        PacingOption,
        TensionOption,
        DialogueDensityOption,
        DescriptionRichnessOption
    } from "$lib/types";
    import {
        PARAM_DESCRIPTIONS,
        LENGTH_PRESETS,
        PACING_OPTIONS,
        TENSION_OPTIONS,
        DIALOGUE_OPTIONS,
        DESCRIPTION_OPTIONS
    } from "$lib/types";

    // Props - all parameters bound bidirectionally
    export let targetLengthPreset: LengthPreset | null = null;
    export let targetLengthWords: number | null = null;

    export let temperature: number = 0.7;
    export let maxTokens: number = 2000;
    export let topP: number = 0.9;
    export let frequencyPenalty: number = 0.0;
    export let presencePenalty: number = 0.0;
    export let topK: number | null = null;

    export let pacing: PacingOption | null = null;
    export let tensionLevel: TensionOption | null = null;
    export let dialogueDensity: DialogueDensityOption | null = null;
    export let descriptionRichness: DescriptionRichnessOption | null = null;

    // Tab state
    let activeTab: "basic" | "advanced" | "expert" = "basic";

    // Custom length toggle
    let useCustomLength = false;

    $: if (useCustomLength) {
        targetLengthPreset = null;
    } else {
        targetLengthWords = null;
    }

    // Helper to toggle selection (click again to deselect)
    function toggleOption<T>(current: T | null, value: T): T | null {
        return current === value ? null : value;
    }
</script>

<div class="ai-parameter-tabs">
    <!-- Tab Navigation -->
    <div class="flex border-b border-gray-200 dark:border-gray-700 mb-4">
        <button
            type="button"
            class="tab-btn"
            class:active={activeTab === "basic"}
            on:click={() => (activeTab = "basic")}
        >
            Basic
        </button>
        <button
            type="button"
            class="tab-btn"
            class:active={activeTab === "advanced"}
            on:click={() => (activeTab = "advanced")}
        >
            Advanced
        </button>
        <button
            type="button"
            class="tab-btn"
            class:active={activeTab === "expert"}
            on:click={() => (activeTab = "expert")}
        >
            Expert
        </button>
    </div>

    <!-- BASIC TAB: Length Control -->
    {#if activeTab === "basic"}
        <div class="space-y-4">
            <h4 class="text-sm font-medium text-gray-700 dark:text-gray-300">
                Output Length
            </h4>

            <!-- Preset Buttons -->
            {#if !useCustomLength}
                <div class="flex gap-2">
                    {#each LENGTH_PRESETS as preset}
                        <button
                            type="button"
                            on:click={() =>
                                (targetLengthPreset = toggleOption(
                                    targetLengthPreset,
                                    preset.value
                                ))}
                            class="flex-1 px-3 py-2 text-sm rounded-md border transition-colors
                                {targetLengthPreset === preset.value
                                ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 text-indigo-900 dark:text-indigo-100'
                                : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400'}"
                        >
                            <span class="block font-medium">{preset.label}</span>
                            <span class="block text-xs text-gray-500 dark:text-gray-400"
                                >{preset.description}</span
                            >
                        </button>
                    {/each}
                </div>
            {/if}

            <!-- Custom Word Count -->
            <div class="flex items-center gap-2">
                <input
                    type="checkbox"
                    id="custom-length"
                    bind:checked={useCustomLength}
                    class="rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500"
                />
                <label
                    for="custom-length"
                    class="text-sm text-gray-600 dark:text-gray-400"
                >
                    Custom word count
                </label>
            </div>

            {#if useCustomLength}
                <div>
                    <input
                        type="number"
                        bind:value={targetLengthWords}
                        min="100"
                        max="10000"
                        step="100"
                        placeholder="e.g., 750"
                        class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white focus:border-indigo-500 focus:ring-indigo-500"
                    />
                    <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        100 - 10,000 words
                    </p>
                </div>
            {/if}
        </div>
    {/if}

    <!-- ADVANCED TAB: LLM Parameters -->
    {#if activeTab === "advanced"}
        <div class="space-y-4">
            <!-- Temperature -->
            <div>
                <div class="flex justify-between items-center mb-1">
                    <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                        Temperature: {temperature.toFixed(1)}
                    </label>
                    <span
                        class="text-xs text-gray-500 cursor-help"
                        title={PARAM_DESCRIPTIONS.temperature}>?</span
                    >
                </div>
                <input
                    type="range"
                    bind:value={temperature}
                    min="0"
                    max="2"
                    step="0.1"
                    class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400">
                    Low = focused, High = creative
                </p>
            </div>

            <!-- Max Tokens -->
            <div>
                <div class="flex justify-between items-center mb-1">
                    <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                        Max Tokens
                    </label>
                    <span
                        class="text-xs text-gray-500 cursor-help"
                        title={PARAM_DESCRIPTIONS.max_tokens}>?</span
                    >
                </div>
                <input
                    type="number"
                    bind:value={maxTokens}
                    min="100"
                    max="32000"
                    step="500"
                    class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
            </div>

            <!-- Top P -->
            <div>
                <div class="flex justify-between items-center mb-1">
                    <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                        Top P: {topP.toFixed(2)}
                    </label>
                    <span
                        class="text-xs text-gray-500 cursor-help"
                        title={PARAM_DESCRIPTIONS.top_p}>?</span
                    >
                </div>
                <input
                    type="range"
                    bind:value={topP}
                    min="0"
                    max="1"
                    step="0.05"
                    class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400">
                    Nucleus sampling threshold
                </p>
            </div>

            <!-- Frequency Penalty -->
            <div>
                <div class="flex justify-between items-center mb-1">
                    <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                        Frequency Penalty: {frequencyPenalty.toFixed(1)}
                    </label>
                    <span
                        class="text-xs text-gray-500 cursor-help"
                        title={PARAM_DESCRIPTIONS.frequency_penalty}>?</span
                    >
                </div>
                <input
                    type="range"
                    bind:value={frequencyPenalty}
                    min="-2"
                    max="2"
                    step="0.1"
                    class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400">
                    Reduces word repetition
                </p>
            </div>

            <!-- Presence Penalty -->
            <div>
                <div class="flex justify-between items-center mb-1">
                    <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                        Presence Penalty: {presencePenalty.toFixed(1)}
                    </label>
                    <span
                        class="text-xs text-gray-500 cursor-help"
                        title={PARAM_DESCRIPTIONS.presence_penalty}>?</span
                    >
                </div>
                <input
                    type="range"
                    bind:value={presencePenalty}
                    min="-2"
                    max="2"
                    step="0.1"
                    class="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                />
                <p class="text-xs text-gray-500 dark:text-gray-400">
                    Encourages new topics
                </p>
            </div>

            <!-- Top K (optional) -->
            <div>
                <div class="flex justify-between items-center mb-1">
                    <label
                        class="text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                        Top K (optional)
                    </label>
                    <span
                        class="text-xs text-gray-500 cursor-help"
                        title={PARAM_DESCRIPTIONS.top_k}>?</span
                    >
                </div>
                <input
                    type="number"
                    bind:value={topK}
                    min="1"
                    max="100"
                    placeholder="Leave empty for default"
                    class="w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white"
                />
            </div>
        </div>
    {/if}

    <!-- EXPERT TAB: Narrative Style -->
    {#if activeTab === "expert"}
        <div class="space-y-4">
            <!-- Pacing -->
            <div>
                <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Pacing
                    <span
                        class="text-xs text-gray-500 ml-1 cursor-help"
                        title={PARAM_DESCRIPTIONS.pacing}>?</span
                    >
                </label>
                <div class="flex gap-2">
                    {#each PACING_OPTIONS as opt}
                        <button
                            type="button"
                            on:click={() =>
                                (pacing = toggleOption(pacing, opt.value))}
                            class="flex-1 px-2 py-2 text-xs rounded-md border transition-colors
                                {pacing === opt.value
                                ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 text-indigo-900 dark:text-indigo-100'
                                : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400'}"
                        >
                            {opt.emoji} {opt.label}
                        </button>
                    {/each}
                </div>
            </div>

            <!-- Tension Level -->
            <div>
                <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Tension Level
                    <span
                        class="text-xs text-gray-500 ml-1 cursor-help"
                        title={PARAM_DESCRIPTIONS.tension_level}>?</span
                    >
                </label>
                <div class="flex gap-2">
                    {#each TENSION_OPTIONS as opt}
                        <button
                            type="button"
                            on:click={() =>
                                (tensionLevel = toggleOption(
                                    tensionLevel,
                                    opt.value
                                ))}
                            class="flex-1 px-2 py-2 text-xs rounded-md border transition-colors
                                {tensionLevel === opt.value
                                ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 text-indigo-900 dark:text-indigo-100'
                                : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400'}"
                        >
                            {opt.emoji} {opt.label}
                        </button>
                    {/each}
                </div>
            </div>

            <!-- Dialogue Density -->
            <div>
                <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Dialogue Density
                    <span
                        class="text-xs text-gray-500 ml-1 cursor-help"
                        title={PARAM_DESCRIPTIONS.dialogue_density}>?</span
                    >
                </label>
                <div class="flex gap-2">
                    {#each DIALOGUE_OPTIONS as opt}
                        <button
                            type="button"
                            on:click={() =>
                                (dialogueDensity = toggleOption(
                                    dialogueDensity,
                                    opt.value
                                ))}
                            class="flex-1 px-2 py-2 text-xs rounded-md border transition-colors
                                {dialogueDensity === opt.value
                                ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 text-indigo-900 dark:text-indigo-100'
                                : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400'}"
                        >
                            {opt.emoji} {opt.label}
                        </button>
                    {/each}
                </div>
            </div>

            <!-- Description Richness -->
            <div>
                <label
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Description Richness
                    <span
                        class="text-xs text-gray-500 ml-1 cursor-help"
                        title={PARAM_DESCRIPTIONS.description_richness}>?</span
                    >
                </label>
                <div class="flex gap-2">
                    {#each DESCRIPTION_OPTIONS as opt}
                        <button
                            type="button"
                            on:click={() =>
                                (descriptionRichness = toggleOption(
                                    descriptionRichness,
                                    opt.value
                                ))}
                            class="flex-1 px-2 py-2 text-xs rounded-md border transition-colors
                                {descriptionRichness === opt.value
                                ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 text-indigo-900 dark:text-indigo-100'
                                : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-400'}"
                        >
                            {opt.emoji} {opt.label}
                        </button>
                    {/each}
                </div>
            </div>
        </div>
    {/if}
</div>

<style>
    .tab-btn {
        @apply px-4 py-2 text-sm font-medium text-gray-500 dark:text-gray-400
            border-b-2 border-transparent hover:text-gray-700 dark:hover:text-gray-200
            transition-colors;
    }
    .tab-btn.active {
        @apply text-indigo-600 dark:text-indigo-400 border-indigo-600 dark:border-indigo-400;
    }
</style>
