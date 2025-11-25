<script lang="ts">
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import type {
        AuthoringMode,
        BeatResponse,
        GenerateBeatRequest,
        LengthPreset,
        PacingOption,
        TensionOption,
        DialogueDensityOption,
        DescriptionRichnessOption
    } from "$lib/types";
    import CollaborativeProposalPanel from './CollaborativeProposalPanel.svelte';
    import AIParameterTabs from './AIParameterTabs.svelte';

    export let storyId: string;
    export let worldId: string;
    export let storyMode: AuthoringMode = "manual";
    export let onBeatGenerated: () => void;

    interface ExistingBeat {
        id: string;
        order_index: number;
        summary: string | null;
        content: string;
    }

    // Initialize generation parameters from user settings
    $: userSettings = $auth.user?.settings;
    $: provider = (userSettings?.llm_provider as "openai" | "anthropic" | "ollama") || "openai";
    $: model = userSettings?.llm_model || "";
    $: ollama_host = userSettings?.llm_base_url || "";
    let user_instructions = "";

    // Basic Tab: Length control
    let targetLengthPreset: LengthPreset | null = null;
    let targetLengthWords: number | null = null;

    // Advanced Tab: LLM parameters
    let temperature = 0.7;
    let max_tokens = 8000;
    let topP = 0.9;
    let frequencyPenalty = 0.0;
    let presencePenalty = 0.0;
    let topK: number | null = null;

    // Expert Tab: Narrative style
    let pacing: PacingOption | null = null;
    let tensionLevel: TensionOption | null = null;
    let dialogueDensity: DialogueDensityOption | null = null;
    let descriptionRichness: DescriptionRichnessOption | null = null;

    // Beat insertion controls
    let insertionMode: string = "append"; // "append" | "insert_after" | "insert_at"
    let insertAfterBeatId: string = "";
    let insertAtPosition: number = 1;
    let existingBeats: ExistingBeat[] = [];
    let loadingBeats: boolean = false;

    // UI state
    let loading = false;
    let error = "";
    let generatedBeat: BeatResponse | null = null;
    let streaming = false;  // Enable streaming mode
    let streamingContent = "";  // Progressive content during streaming
    let streamingMetadata: { summary?: string; time_label?: string; reasoning?: string } = {};

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

    async function loadExistingBeats() {
        loadingBeats = true;
        try {
            const beats = await api.get<ExistingBeat[]>(`/stories/${storyId}/beats`);
            existingBeats = beats.sort((a, b) => a.order_index - b.order_index);
        } catch (e: any) {
            console.error("Failed to load beats:", e);
            existingBeats = [];
        } finally {
            loadingBeats = false;
        }
    }

    // Load beats when component mounts
    loadExistingBeats();

    async function handleGenerate() {
        if (streaming) {
            await handleStreamingGenerate();
        } else {
            await handleStandardGenerate();
        }
    }

    async function handleStandardGenerate() {
        loading = true;
        error = "";
        generatedBeat = null;

        try {
            const requestBody: GenerateBeatRequest = {
                provider,
                insertion_mode: insertionMode,
                // Advanced Tab: LLM parameters
                temperature,
                max_tokens,
                top_p: topP,
                frequency_penalty: frequencyPenalty,
                presence_penalty: presencePenalty,
            };

            // Basic Tab: Length control (only include if set)
            if (targetLengthPreset) requestBody.target_length_preset = targetLengthPreset;
            if (targetLengthWords) requestBody.target_length_words = targetLengthWords;

            // Advanced Tab: Optional top_k
            if (topK !== null) requestBody.top_k = topK;

            // Expert Tab: Narrative style (only include if set)
            if (pacing) requestBody.pacing = pacing;
            if (tensionLevel) requestBody.tension_level = tensionLevel;
            if (dialogueDensity) requestBody.dialogue_density = dialogueDensity;
            if (descriptionRichness) requestBody.description_richness = descriptionRichness;

            // Add optional fields
            if (model) requestBody.model = model;
            if (user_instructions) requestBody.user_instructions = user_instructions;
            if (provider === "ollama" && ollama_host) {
                requestBody.ollama_host = ollama_host;
            }

            // Add insertion parameters based on mode
            if (insertionMode === "insert_after") {
                requestBody.insert_after_beat_id = insertAfterBeatId || null;
            } else if (insertionMode === "insert_at") {
                requestBody.insert_at_position = insertAtPosition;
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

    async function handleStreamingGenerate() {
        loading = true;
        error = "";
        generatedBeat = null;
        streamingContent = "";
        streamingMetadata = {};

        try {
            const requestBody: GenerateBeatRequest = {
                provider,
                insertion_mode: insertionMode,
                // Advanced Tab: LLM parameters
                temperature,
                max_tokens,
                top_p: topP,
                frequency_penalty: frequencyPenalty,
                presence_penalty: presencePenalty,
            };

            // Basic Tab: Length control (only include if set)
            if (targetLengthPreset) requestBody.target_length_preset = targetLengthPreset;
            if (targetLengthWords) requestBody.target_length_words = targetLengthWords;

            // Advanced Tab: Optional top_k
            if (topK !== null) requestBody.top_k = topK;

            // Expert Tab: Narrative style (only include if set)
            if (pacing) requestBody.pacing = pacing;
            if (tensionLevel) requestBody.tension_level = tensionLevel;
            if (dialogueDensity) requestBody.dialogue_density = dialogueDensity;
            if (descriptionRichness) requestBody.description_richness = descriptionRichness;

            // Add optional fields
            if (model) requestBody.model = model;
            if (user_instructions) requestBody.user_instructions = user_instructions;
            if (provider === "ollama" && ollama_host) {
                requestBody.ollama_host = ollama_host;
            }

            // Add insertion parameters based on mode
            if (insertionMode === "insert_after") {
                requestBody.insert_after_beat_id = insertAfterBeatId || null;
            } else if (insertionMode === "insert_at") {
                requestBody.insert_at_position = insertAtPosition;
            }

            // Use fetch directly for SSE streaming
            const token = $auth.token;
            const baseUrl = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
            const response = await fetch(
                `${baseUrl}/api/v1/narrative/stories/${storyId}/beats/generate/stream`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify(requestBody),
                }
            );

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || "Streaming generation failed");
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error("Response body is not readable");
            }

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split("\n");

                for (const line of lines) {
                    if (line.startsWith("data: ")) {
                        const data = line.slice(6);
                        try {
                            const event = JSON.parse(data);

                            if (event.type === "token") {
                                // Append progressive content
                                streamingContent += event.content;
                            } else if (event.type === "metadata") {
                                // Store metadata
                                streamingMetadata = {
                                    summary: event.summary,
                                    time_label: event.time_label,
                                    reasoning: event.reasoning,
                                };
                            } else if (event.type === "complete") {
                                // Store final beat data
                                generatedBeat = event.beat;
                            } else if (event.type === "error") {
                                throw new Error(event.message);
                            }
                        } catch (parseError) {
                            console.error("Failed to parse SSE event:", parseError);
                        }
                    }
                }
            }

            // In autonomous mode, immediately trigger refresh
            if (storyMode === "autonomous") {
                onBeatGenerated();
            }
        } catch (e: any) {
            error = e.message || "Failed to stream beat generation";
        } finally {
            loading = false;
        }
    }

    function handleAccept() {
        // Beat is already saved in the database by the API
        // Just clear and refresh
        generatedBeat = null;
        streamingContent = "";
        streamingMetadata = {};
        user_instructions = "";
        onBeatGenerated();
    }

    function handleRegenerate() {
        // Clear streaming state before regenerating
        streamingContent = "";
        streamingMetadata = {};
        generatedBeat = null;
        handleGenerate();
    }

    function handleDiscard() {
        // TODO: Implement delete beat endpoint
        // For now, just clear the generated beat
        generatedBeat = null;
        streamingContent = "";
        streamingMetadata = {};
        error = "Beat discard not yet implemented. Please delete manually from the beats list.";
    }
</script>

<div class="bg-white dark:bg-gray-800 shadow-sm ring-1 ring-gray-900/5 dark:ring-gray-700 rounded-lg overflow-hidden">
    <!-- Mode-Specific Header -->
    <div class="{storyMode === 'autonomous' ? 'bg-indigo-500' : storyMode === 'collaborative' ? 'bg-purple-500' : 'bg-green-500'} px-6 py-4 text-white">
        <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
                <span class="text-2xl">
                    {#if storyMode === "autonomous"}
                        🤖
                    {:else if storyMode === "collaborative"}
                        🤝
                    {:else}
                        ✍️
                    {/if}
                </span>
                <div>
                    <h3 class="text-base font-semibold">
                        {#if storyMode === "autonomous"}
                            Autonomous Generation
                        {:else if storyMode === "collaborative"}
                            Collaborative Mode
                        {:else}
                            Manual Authoring with AI Assist
                        {/if}
                    </h3>
                    <p class="text-xs text-white/80 mt-0.5">
                        {#if storyMode === "autonomous"}
                            AI creates complete beats automatically
                        {:else if storyMode === "collaborative"}
                            Choose from multiple AI proposals
                        {:else}
                            Get AI help when you need it
                        {/if}
                    </p>
                </div>
            </div>
            <span class="inline-flex items-center rounded-md bg-white/20 px-2 py-1 text-xs font-medium">
                {storyMode}
            </span>
        </div>
    </div>

    <div class="p-6">

    {#if storyMode === "collaborative" && !generatedBeat}
        <!-- Collaborative Mode: Use multi-proposal panel -->
        <CollaborativeProposalPanel
            {storyId}
            {worldId}
            onProposalUsed={handleAccept}
        />
    {:else if !generatedBeat}
        <form on:submit|preventDefault={handleGenerate} class="space-y-4">
            <!-- Provider Selection -->
            <div>
                <label
                    for="provider"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                    LLM Provider
                </label>
                <select
                    id="provider"
                    bind:value={provider}
                    class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="ollama">Ollama</option>
                </select>
            </div>

            <!-- Model Override -->
            <div>
                <label for="model" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                    Model {provider !== "ollama" ? "(optional)" : ""}
                </label>
                <input
                    type="text"
                    id="model"
                    bind:value={model}
                    placeholder={getModelPlaceholder(provider)}
                    class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                />
            </div>

            <!-- Ollama Host (only for Ollama) -->
            {#if provider === "ollama"}
                <div>
                    <label
                        for="ollama_host"
                        class="block text-sm font-medium text-gray-700 dark:text-gray-300"
                    >
                        Ollama Server URL <span class="text-red-500 dark:text-red-400">*</span>
                    </label>
                    <input
                        type="url"
                        id="ollama_host"
                        bind:value={ollama_host}
                        placeholder="e.g., http://192.168.1.100:11434"
                        required={provider === "ollama"}
                        class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                    />
                    <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        URL of your Ollama server (e.g., Windows PC on network)
                    </p>
                </div>
            {/if}

            <!-- User Instructions (Collaborative/Manual modes) -->
            {#if storyMode !== "autonomous"}
                <div>
                    <label
                        for="instructions"
                        class="block text-sm font-medium text-gray-700 dark:text-gray-300"
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
                        class="mt-1 block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                    ></textarea>
                </div>
            {/if}

            <!-- Beat Position Controls -->
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Insert Position
                </label>
                <div class="space-y-3">
                    <!-- Insertion mode selector -->
                    <div class="flex gap-2">
                        <button
                            type="button"
                            on:click={() => insertionMode = "append"}
                            class="flex-1 px-3 py-2 text-sm rounded-md border {insertionMode === 'append' ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 dark:border-indigo-400 text-indigo-900 dark:text-indigo-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'}"
                        >
                            📄 End of story
                        </button>
                        <button
                            type="button"
                            on:click={() => insertionMode = "insert_after"}
                            class="flex-1 px-3 py-2 text-sm rounded-md border {insertionMode === 'insert_after' ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 dark:border-indigo-400 text-indigo-900 dark:text-indigo-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'}"
                        >
                            ➡️ After beat
                        </button>
                        <button
                            type="button"
                            on:click={() => insertionMode = "insert_at"}
                            class="flex-1 px-3 py-2 text-sm rounded-md border {insertionMode === 'insert_at' ? 'bg-indigo-100 dark:bg-indigo-900/30 border-indigo-500 dark:border-indigo-400 text-indigo-900 dark:text-indigo-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'}"
                        >
                            #️⃣ At position
                        </button>
                    </div>

                    <!-- Insert after beat selector -->
                    {#if insertionMode === "insert_after"}
                        <select
                            bind:value={insertAfterBeatId}
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400"
                        >
                            <option value="">Select a beat...</option>
                            {#each existingBeats as beat}
                                <option value={beat.id}>
                                    Beat #{beat.order_index}: {beat.summary || beat.content.substring(0, 50)}...
                                </option>
                            {/each}
                        </select>
                        {#if loadingBeats}
                            <p class="text-xs text-gray-500 dark:text-gray-400">Loading beats...</p>
                        {:else if existingBeats.length === 0}
                            <p class="text-xs text-amber-600 dark:text-amber-400">No existing beats. Will insert at beginning.</p>
                        {/if}
                    {/if}

                    <!-- Insert at position input -->
                    {#if insertionMode === "insert_at"}
                        <div class="flex items-center gap-2">
                            <input
                                type="number"
                                bind:value={insertAtPosition}
                                min="1"
                                max={existingBeats.length + 1}
                                class="flex-1 rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400"
                            />
                            <span class="text-sm text-gray-500 dark:text-gray-400">
                                (1 to {existingBeats.length + 1})
                            </span>
                        </div>
                        <p class="text-xs text-gray-500 dark:text-gray-400">
                            Position 1 = first beat, {existingBeats.length + 1} = last beat
                        </p>
                    {/if}
                </div>
            </div>

            <!-- Streaming Mode Toggle -->
            <div class="flex items-center">
                <input
                    type="checkbox"
                    id="streaming"
                    bind:checked={streaming}
                    class="h-4 w-4 rounded border-gray-300 dark:border-gray-600 text-indigo-600 dark:text-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400"
                />
                <label
                    for="streaming"
                    class="ml-2 block text-sm text-gray-700 dark:text-gray-300"
                >
                    Enable streaming (see generation live)
                </label>
            </div>

            <!-- AI Parameter Tabs (Basic/Advanced/Expert) -->
            <AIParameterTabs
                bind:targetLengthPreset
                bind:targetLengthWords
                bind:temperature
                bind:maxTokens={max_tokens}
                bind:topP
                bind:frequencyPenalty
                bind:presencePenalty
                bind:topK
                bind:pacing
                bind:tensionLevel
                bind:dialogueDensity
                bind:descriptionRichness
            />

            <!-- Streaming Content Display (while generating) -->
            {#if loading && streaming && streamingContent}
                <div class="rounded-md bg-indigo-50 dark:bg-indigo-900/30 p-4 border border-indigo-200 dark:border-indigo-700">
                    <div class="flex items-center gap-2 mb-3">
                        <div class="animate-pulse flex items-center">
                            <div class="h-2 w-2 bg-indigo-600 dark:bg-indigo-400 rounded-full mr-1"></div>
                            <div class="h-2 w-2 bg-indigo-600 dark:bg-indigo-400 rounded-full mr-1 animation-delay-200"></div>
                            <div class="h-2 w-2 bg-indigo-600 dark:bg-indigo-400 rounded-full animation-delay-400"></div>
                        </div>
                        <p class="text-xs font-medium text-indigo-700 dark:text-indigo-300">
                            Generating...
                        </p>
                    </div>
                    <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">
                        {streamingContent}<span class="animate-pulse">▊</span>
                    </p>

                    {#if streamingMetadata.summary}
                        <div class="mt-3 pt-3 border-t border-indigo-300 dark:border-indigo-700">
                            <p class="text-xs font-medium text-indigo-600 dark:text-indigo-400 mb-1">
                                Summary:
                            </p>
                            <p class="text-xs text-gray-600 dark:text-gray-400">
                                {streamingMetadata.summary}
                            </p>
                        </div>
                    {/if}

                    {#if streamingMetadata.time_label}
                        <div class="mt-2">
                            <span class="inline-flex items-center rounded-md bg-indigo-100 dark:bg-indigo-800 px-2 py-1 text-xs text-indigo-700 dark:text-indigo-300">
                                📅 {streamingMetadata.time_label}
                            </span>
                        </div>
                    {/if}
                </div>
            {/if}

            <!-- Error Display -->
            {#if error}
                <div class="rounded-md bg-red-50 dark:bg-red-900/30 p-4">
                    <p class="text-sm text-red-800 dark:text-red-300">{error}</p>
                </div>
            {/if}

            <!-- Generate Button -->
            <div class="flex justify-end">
                <button
                    type="submit"
                    disabled={loading || (provider === "ollama" && !ollama_host)}
                    class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 disabled:opacity-50"
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
            <div class="rounded-md bg-gray-50 dark:bg-gray-700 p-4 border border-gray-200 dark:border-gray-600">
                <div class="flex items-start justify-between mb-2">
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Generated Beat
                    </h4>
                    <div class="flex gap-1">
                        <span class="inline-flex items-center rounded-md bg-blue-50 dark:bg-blue-900/30 px-2 py-1 text-xs font-medium text-blue-700 dark:text-blue-300">
                            {provider}
                        </span>
                        {#if generatedBeat.generated_by}
                            <span class="inline-flex items-center rounded-md bg-green-50 dark:bg-green-900/30 px-2 py-1 text-xs font-medium text-green-700 dark:text-green-300">
                                {generatedBeat.generated_by}
                            </span>
                        {/if}
                    </div>
                </div>

                <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                    {generatedBeat.content}
                </p>

                {#if generatedBeat.summary}
                    <div class="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                        <p class="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Summary:</p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">{generatedBeat.summary}</p>
                    </div>
                {/if}

                {#if generatedBeat.local_time_label}
                    <div class="mt-2">
                        <span class="inline-flex items-center rounded-md bg-gray-100 dark:bg-gray-600 px-2 py-1 text-xs text-gray-600 dark:text-gray-300">
                            📅 {generatedBeat.local_time_label}
                        </span>
                    </div>
                {/if}

                {#if generatedBeat.generation_reasoning}
                    <div class="mt-3 pt-3 border-t border-gray-300 dark:border-gray-600">
                        <div class="flex items-center gap-2 mb-2">
                            <svg
                                class="w-4 h-4 text-indigo-600 dark:text-indigo-400"
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
                            <p class="text-xs font-medium text-gray-500 dark:text-gray-400">AI Thoughts:</p>
                        </div>
                        <p class="text-xs text-gray-600 dark:text-gray-300 bg-indigo-50 dark:bg-indigo-900/30 p-2 rounded border border-indigo-200 dark:border-indigo-700">
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
                        class="rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
                    >
                        Discard
                    </button>
                    <button
                        on:click={handleRegenerate}
                        class="rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
                    >
                        Regenerate
                    </button>
                    <button
                        on:click={handleAccept}
                        class="rounded-md bg-green-600 dark:bg-green-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 dark:hover:bg-green-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 dark:focus-visible:outline-green-400"
                    >
                        Accept & Save
                    </button>
                </div>
            {/if}
        </div>
    {/if}
    </div>
</div>
