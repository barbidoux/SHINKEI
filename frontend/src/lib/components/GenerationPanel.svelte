<script lang="ts">
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import type { AuthoringMode, BeatResponse, GenerateBeatRequest } from "$lib/types";

    export let storyId: string;
    export let storyMode: AuthoringMode = "manual";
    export let onBeatGenerated: () => void;

    // Initialize generation parameters from user settings
    $: userSettings = $auth.user?.settings;
    $: provider = (userSettings?.llm_provider as "openai" | "anthropic" | "ollama") || "openai";
    $: model = userSettings?.llm_model || "";
    $: ollama_host = userSettings?.llm_base_url || "";
    let user_instructions = "";
    let temperature = 0.7;
    let max_tokens = 8000;

    // UI state
    let loading = false;
    let error = "";
    let generatedBeat: BeatResponse | null = null;

    // Get placeholders based on provider
    function getModelPlaceholder(p: string): string {
        switch (p) {
            case "openai":
                return "e.g., gpt-4o (leave empty for default)";
            case "anthropic":
                return "e.g., claude-3-5-sonnet-20240620";
            case "ollama":
                return "e.g., llama3, mistral";
            default:
                return "Model name";
        }
    }

    async function handleGenerate() {
        loading = true;
        error = "";
        generatedBeat = null;

        try {
            const requestBody: GenerateBeatRequest = {
                provider,
                temperature,
                max_tokens,
            };

            // Add optional fields
            if (model) requestBody.model = model;
            if (user_instructions) requestBody.user_instructions = user_instructions;
            if (provider === "ollama" && ollama_host) {
                requestBody.ollama_host = ollama_host;
            }

            const response = await api.post<BeatResponse>(
                `/narrative/stories/${storyId}/beats/generate`,
                requestBody
            );

            generatedBeat = response;

            // In autonomous mode, immediately trigger refresh
            if (storyMode === "autonomous") {
                onBeatGenerated();
            }
        } catch (e: any) {
            error = e.message || "Failed to generate beat";
        } finally {
            loading = false;
        }
    }

    function handleAccept() {
        // Beat is already saved in the database by the API
        // Just clear and refresh
        generatedBeat = null;
        user_instructions = "";
        onBeatGenerated();
    }

    function handleRegenerate() {
        handleGenerate();
    }

    function handleDiscard() {
        // TODO: Implement delete beat endpoint
        // For now, just clear the generated beat
        generatedBeat = null;
        error = "Beat discard not yet implemented. Please delete manually from the beats list.";
    }
</script>

<div class="bg-white shadow-sm ring-1 ring-gray-900/5 rounded-lg p-6">
    <div class="flex items-center justify-between mb-4">
        <h3 class="text-base font-semibold text-gray-900">
            {#if storyMode === "autonomous"}
                AI Generation (Autonomous Mode)
            {:else if storyMode === "collaborative"}
                AI Collaboration
            {:else}
                AI Assistance
            {/if}
        </h3>
        <span class="inline-flex items-center rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700">
            {storyMode}
        </span>
    </div>

    {#if !generatedBeat}
        <form on:submit|preventDefault={handleGenerate} class="space-y-4">
            <!-- Provider Selection -->
            <div>
                <label
                    for="provider"
                    class="block text-sm font-medium text-gray-700"
                >
                    LLM Provider
                </label>
                <select
                    id="provider"
                    bind:value={provider}
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="ollama">Ollama</option>
                </select>
            </div>

            <!-- Model Override -->
            <div>
                <label for="model" class="block text-sm font-medium text-gray-700">
                    Model {provider !== "ollama" ? "(optional)" : ""}
                </label>
                <input
                    type="text"
                    id="model"
                    bind:value={model}
                    placeholder={getModelPlaceholder(provider)}
                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
            </div>

            <!-- Ollama Host (only for Ollama) -->
            {#if provider === "ollama"}
                <div>
                    <label
                        for="ollama_host"
                        class="block text-sm font-medium text-gray-700"
                    >
                        Ollama Server URL <span class="text-red-500">*</span>
                    </label>
                    <input
                        type="url"
                        id="ollama_host"
                        bind:value={ollama_host}
                        placeholder="e.g., http://192.168.1.100:11434"
                        required={provider === "ollama"}
                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                    <p class="mt-1 text-xs text-gray-500">
                        URL of your Ollama server (e.g., Windows PC on network)
                    </p>
                </div>
            {/if}

            <!-- User Instructions (Collaborative/Manual modes) -->
            {#if storyMode !== "autonomous"}
                <div>
                    <label
                        for="instructions"
                        class="block text-sm font-medium text-gray-700"
                    >
                        {storyMode === "collaborative" ? "Guidance" : "Request"}
                    </label>
                    <textarea
                        id="instructions"
                        rows="3"
                        bind:value={user_instructions}
                        placeholder={storyMode === "collaborative"
                            ? "Describe what should happen next..."
                            : "Ask for suggestions or improvements..."}
                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    ></textarea>
                </div>
            {/if}

            <!-- Advanced Parameters -->
            <details class="mt-4">
                <summary
                    class="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900"
                >
                    Advanced Parameters
                </summary>
                <div class="mt-3 space-y-4 pl-4 border-l-2 border-gray-200">
                    <!-- Temperature -->
                    <div>
                        <label
                            for="temperature"
                            class="block text-sm font-medium text-gray-700"
                        >
                            Temperature: {temperature}
                        </label>
                        <input
                            type="range"
                            id="temperature"
                            bind:value={temperature}
                            min="0"
                            max="2"
                            step="0.1"
                            class="mt-1 block w-full"
                        />
                        <p class="mt-1 text-xs text-gray-500">
                            Lower = more focused, Higher = more creative
                        </p>
                    </div>

                    <!-- Max Tokens -->
                    <div>
                        <label
                            for="max_tokens"
                            class="block text-sm font-medium text-gray-700"
                        >
                            Max Tokens
                        </label>
                        <input
                            type="number"
                            id="max_tokens"
                            bind:value={max_tokens}
                            min="100"
                            max="32000"
                            step="500"
                            class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                        />
                        <p class="mt-1 text-xs text-gray-500">
                            Maximum tokens to generate (up to 32K for long-form content)
                        </p>
                    </div>
                </div>
            </details>

            <!-- Error Display -->
            {#if error}
                <div class="rounded-md bg-red-50 p-4">
                    <p class="text-sm text-red-800">{error}</p>
                </div>
            {/if}

            <!-- Generate Button -->
            <div class="flex justify-end">
                <button
                    type="submit"
                    disabled={loading || (provider === "ollama" && !ollama_host)}
                    class="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                >
                    {#if loading}
                        Generating...
                    {:else if storyMode === "autonomous"}
                        Generate Beat
                    {:else if storyMode === "collaborative"}
                        Propose Beat
                    {:else}
                        Get Suggestion
                    {/if}
                </button>
            </div>
        </form>
    {:else}
        <!-- Generated Beat Preview (Collaborative/Manual modes) -->
        <div class="space-y-4">
            <div class="rounded-md bg-gray-50 p-4 border border-gray-200">
                <div class="flex items-start justify-between mb-2">
                    <h4 class="text-sm font-medium text-gray-900">
                        Generated Beat
                    </h4>
                    <div class="flex gap-1">
                        <span class="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
                            {provider}
                        </span>
                        {#if generatedBeat.generated_by}
                            <span class="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700">
                                {generatedBeat.generated_by}
                            </span>
                        {/if}
                    </div>
                </div>

                <p class="text-sm text-gray-700 whitespace-pre-wrap">
                    {generatedBeat.content}
                </p>

                {#if generatedBeat.summary}
                    <div class="mt-3 pt-3 border-t border-gray-300">
                        <p class="text-xs font-medium text-gray-500 mb-1">Summary:</p>
                        <p class="text-xs text-gray-600">{generatedBeat.summary}</p>
                    </div>
                {/if}

                {#if generatedBeat.local_time_label}
                    <div class="mt-2">
                        <span class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-600">
                            📅 {generatedBeat.local_time_label}
                        </span>
                    </div>
                {/if}

                {#if generatedBeat.generation_reasoning}
                    <div class="mt-3 pt-3 border-t border-gray-300">
                        <div class="flex items-center gap-2 mb-2">
                            <svg
                                class="w-4 h-4 text-indigo-600"
                                fill="none"
                                stroke="currentColor"
                                viewBox="0 0 24 24"
                            >
                                <path
                                    stroke-linecap="round"
                                    stroke-linejoin="round"
                                    stroke-width="2"
                                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                                />
                            </svg>
                            <p class="text-xs font-medium text-gray-500">AI Thoughts:</p>
                        </div>
                        <p class="text-xs text-gray-600 bg-indigo-50 p-2 rounded border border-indigo-200">
                            {generatedBeat.generation_reasoning}
                        </p>
                    </div>
                {/if}
            </div>

            <!-- Action Buttons (Collaborative mode) -->
            {#if storyMode === "collaborative" || storyMode === "manual"}
                <div class="flex justify-end gap-2">
                    <button
                        on:click={handleDiscard}
                        class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                    >
                        Discard
                    </button>
                    <button
                        on:click={handleRegenerate}
                        class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                    >
                        Regenerate
                    </button>
                    <button
                        on:click={handleAccept}
                        class="rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600"
                    >
                        Accept & Save
                    </button>
                </div>
            {/if}
        </div>
    {/if}
</div>
