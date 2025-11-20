<script lang="ts">
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import UnifiedDiffViewer from "./UnifiedDiffViewer.svelte";
    import type { BeatResponse } from "$lib/types";

    export let beat: BeatResponse;
    export let storyId: string;
    export let onModificationApplied: () => void;
    export let onClose: () => void;

    // Initialize from user settings
    $: userSettings = $auth.user?.settings;
    $: provider = (userSettings?.llm_provider as "openai" | "anthropic" | "ollama") || "openai";
    $: model = userSettings?.llm_model || "";
    $: ollama_host = userSettings?.llm_base_url || "";

    let modification_instructions = "";
    let temperature = 0.7;
    let max_tokens = 8000;
    let scope = ["content", "summary", "time_label", "world_event"];

    // UI state
    let loading = false;
    let error = "";
    let modification: any = null;
    let viewMode: "form" | "preview" = "form";

    // Quick action templates
    const quickActions = [
        { label: "Fix grammar & typos", instruction: "Fix any grammar errors, typos, and improve clarity without changing the narrative content." },
        { label: "Make more descriptive", instruction: "Expand this beat with more vivid descriptions and sensory details." },
        { label: "Make more concise", instruction: "Condense this beat while preserving all key narrative points." },
        { label: "Change tone to serious", instruction: "Rewrite this beat with a more serious, dramatic tone." },
        { label: "Change tone to lighthearted", instruction: "Rewrite this beat with a more lighthearted, playful tone." },
        { label: "Add tension", instruction: "Rewrite this beat to increase narrative tension and suspense." },
    ];

    // Template suggestions
    const templates = [
        { category: "Character", example: "Make [character name] more [trait/emotion]" },
        { category: "Pacing", example: "Slow down/speed up the pacing of this scene" },
        { category: "POV", example: "Shift perspective to focus on [character/element]" },
        { category: "Setting", example: "Add more details about the [location/environment]" },
    ];

    function applyQuickAction(instruction: string) {
        modification_instructions = instruction;
    }

    async function handleRequestModification() {
        loading = true;
        error = "";

        try {
            const requestBody = {
                modification_instructions,
                provider,
                model: model || undefined,
                ollama_host: provider === "ollama" ? ollama_host : undefined,
                temperature,
                max_tokens,
                scope,
            };

            const response = await api.post(
                `/narrative/stories/${storyId}/beats/${beat.id}/modifications`,
                requestBody
            );

            modification = response;
            viewMode = "preview";
        } catch (e: any) {
            error = e.message || "Failed to generate modification";
        } finally {
            loading = false;
        }
    }

    async function handleApply() {
        loading = true;
        error = "";

        try {
            await api.post(
                `/narrative/stories/${storyId}/beats/${beat.id}/modifications/${modification.id}/apply`,
                {
                    modification_id: modification.id,
                    apply_content: true,
                    apply_summary: true,
                    apply_time_label: true,
                    apply_world_event: true,
                }
            );

            onModificationApplied();
        } catch (e: any) {
            error = e.message || "Failed to apply modification";
        } finally {
            loading = false;
        }
    }

    function handleRegenerate() {
        modification = null;
        viewMode = "form";
    }

    function handleDiscard() {
        modification = null;
        viewMode = "form";
    }
</script>

<div class="beat-modification-panel bg-white shadow-xl rounded-lg flex flex-col h-full">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <h3 class="text-lg font-semibold text-gray-900">Modify Beat</h3>
        <button
            on:click={onClose}
            class="text-gray-400 hover:text-gray-600 transition-colors"
        >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
        </button>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto px-6 py-4">
        {#if viewMode === "form"}
            <!-- Original Content Display -->
            <div class="mb-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Original Content</h4>
                <p class="text-sm text-gray-800 whitespace-pre-wrap">{beat.content}</p>
                {#if beat.summary}
                    <div class="mt-2 pt-2 border-t border-gray-300">
                        <p class="text-xs text-gray-600">{beat.summary}</p>
                    </div>
                {/if}
            </div>

            <!-- Modification Form -->
            <form on:submit|preventDefault={handleRequestModification} class="space-y-4">
                <!-- Quick Actions -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Quick Actions
                    </label>
                    <div class="flex flex-wrap gap-2">
                        {#each quickActions as action}
                            <button
                                type="button"
                                on:click={() => applyQuickAction(action.instruction)}
                                class="px-3 py-1 text-xs font-medium rounded-md bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors"
                            >
                                {action.label}
                            </button>
                        {/each}
                    </div>
                </div>

                <!-- Template Suggestions -->
                <details class="text-sm">
                    <summary class="cursor-pointer text-gray-700 font-medium hover:text-gray-900">
                        Template Suggestions
                    </summary>
                    <div class="mt-2 space-y-2 pl-4">
                        {#each templates as template}
                            <div class="text-xs">
                                <span class="font-medium text-gray-700">{template.category}:</span>
                                <span class="text-gray-600 italic">{template.example}</span>
                            </div>
                        {/each}
                    </div>
                </details>

                <!-- Freeform Instructions -->
                <div>
                    <label for="instructions" class="block text-sm font-medium text-gray-700">
                        Modification Instructions <span class="text-red-500">*</span>
                    </label>
                    <textarea
                        id="instructions"
                        rows="4"
                        bind:value={modification_instructions}
                        required
                        placeholder="Describe how you want to modify this beat..."
                        class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    ></textarea>
                </div>

                <!-- Scope Selection -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Modify
                    </label>
                    <div class="space-y-2">
                        <label class="flex items-center">
                            <input type="checkbox" bind:group={scope} value="content" class="rounded" />
                            <span class="ml-2 text-sm text-gray-700">Content</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" bind:group={scope} value="summary" class="rounded" />
                            <span class="ml-2 text-sm text-gray-700">Summary</span>
                        </label>
                        <label class="flex items-center">
                            <input type="checkbox" bind:group={scope} value="time_label" class="rounded" />
                            <span class="ml-2 text-sm text-gray-700">Time Label</span>
                        </label>
                    </div>
                </div>

                <!-- Advanced Settings -->
                <details>
                    <summary class="text-sm font-medium text-gray-700 cursor-pointer hover:text-gray-900">
                        Advanced Settings
                    </summary>
                    <div class="mt-3 space-y-4 pl-4">
                        <!-- Provider -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700">
                                LLM Provider
                            </label>
                            <select
                                bind:value={provider}
                                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            >
                                <option value="openai">OpenAI</option>
                                <option value="anthropic">Anthropic (Claude)</option>
                                <option value="ollama">Ollama</option>
                            </select>
                        </div>

                        {#if provider === "ollama"}
                            <div>
                                <label class="block text-sm font-medium text-gray-700">
                                    Ollama Server URL
                                </label>
                                <input
                                    type="url"
                                    bind:value={ollama_host}
                                    placeholder="e.g., http://192.168.1.100:11434"
                                    class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                                />
                            </div>
                        {/if}

                        <!-- Temperature -->
                        <div>
                            <label class="block text-sm font-medium text-gray-700">
                                Temperature: {temperature}
                            </label>
                            <input
                                type="range"
                                bind:value={temperature}
                                min="0"
                                max="2"
                                step="0.1"
                                class="mt-1 block w-full"
                            />
                        </div>
                    </div>
                </details>

                <!-- Error Display -->
                {#if error}
                    <div class="rounded-md bg-red-50 p-4">
                        <p class="text-sm text-red-800">{error}</p>
                    </div>
                {/if}

                <!-- Submit Button -->
                <div class="flex justify-end">
                    <button
                        type="submit"
                        disabled={loading || !modification_instructions}
                        class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                    >
                        {loading ? "Generating..." : "Generate Modification"}
                    </button>
                </div>
            </form>
        {:else if viewMode === "preview" && modification}
            <!-- Modification Preview -->
            <div class="space-y-6">
                <!-- AI Reasoning -->
                {#if modification.reasoning}
                    <div class="bg-indigo-50 rounded-lg p-4 border border-indigo-200">
                        <div class="flex items-center gap-2 mb-2">
                            <svg class="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                            </svg>
                            <h4 class="text-sm font-medium text-indigo-900">AI Reasoning</h4>
                        </div>
                        <p class="text-sm text-indigo-800">{modification.reasoning}</p>
                    </div>
                {/if}

                <!-- Unified Diff -->
                {#if modification.unified_diff}
                    <UnifiedDiffViewer diff={modification.unified_diff} title="Changes Preview" />
                {/if}

                <!-- Modified Content Preview -->
                <div class="bg-green-50 rounded-lg p-4 border border-green-200">
                    <h4 class="text-sm font-medium text-green-900 mb-2">Modified Content</h4>
                    <p class="text-sm text-gray-800 whitespace-pre-wrap">{modification.modified_content}</p>
                    {#if modification.modified_summary}
                        <div class="mt-2 pt-2 border-t border-green-300">
                            <p class="text-xs text-gray-600">{modification.modified_summary}</p>
                        </div>
                    {/if}
                </div>

                <!-- Action Buttons -->
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
                        on:click={handleApply}
                        disabled={loading}
                        class="rounded-md bg-green-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600 disabled:opacity-50"
                    >
                        {loading ? "Applying..." : "Apply Changes"}
                    </button>
                </div>
            </div>
        {/if}
    </div>
</div>

<style>
    .beat-modification-panel {
        max-width: 100%;
    }
</style>
