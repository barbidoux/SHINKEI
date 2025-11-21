<script lang="ts">
    import { api } from "$lib/api";

    export let storyId: string;
    export let beatId: string;

    interface CoherenceIssue {
        type: string;
        severity: "low" | "medium" | "high";
        description: string;
    }

    interface CoherenceResult {
        coherent: boolean;
        issues: CoherenceIssue[];
        suggestions: string[];
        analysis?: string;
    }

    let loading = false;
    let error = "";
    let result: CoherenceResult | null = null;
    let showAnalysis = false;
    let showProviderSelect = false;
    let selectedProvider: "openai" | "anthropic" | "ollama" = "openai";

    async function checkCoherence() {
        loading = true;
        error = "";
        result = null;

        try {
            // Always send the provider to override user's default settings
            const body = {
                provider: selectedProvider
            };

            result = await api.post<CoherenceResult>(
                `/narrative/stories/${storyId}/beats/${beatId}/check-coherence`,
                body
            );
        } catch (e: any) {
            error = e.message || "Failed to check coherence";
        } finally {
            loading = false;
        }
    }

    function getSeverityColor(severity: string): string {
        switch (severity) {
            case "high":
                return "bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700 text-red-800 dark:text-red-300";
            case "medium":
                return "bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-700 text-yellow-800 dark:text-yellow-300";
            case "low":
                return "bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-300";
            default:
                return "bg-gray-50 dark:bg-gray-700 border-gray-200 dark:border-gray-600 text-gray-800 dark:text-gray-300";
        }
    }

    function getSeverityBadge(severity: string): string {
        switch (severity) {
            case "high":
                return "bg-red-100 dark:bg-red-900/50 text-red-800 dark:text-red-300 ring-red-600/20 dark:ring-red-500/30";
            case "medium":
                return "bg-yellow-100 dark:bg-yellow-900/50 text-yellow-800 dark:text-yellow-300 ring-yellow-600/20 dark:ring-yellow-500/30";
            case "low":
                return "bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300 ring-blue-600/20 dark:ring-blue-500/30";
            default:
                return "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300 ring-gray-600/20 dark:ring-gray-500/30";
        }
    }

    function formatIssueType(type: string): string {
        return type
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    }
</script>

<div class="bg-white dark:bg-gray-800 shadow-sm ring-1 ring-gray-900/5 dark:ring-gray-700 rounded-lg p-6">
    <div class="space-y-3 mb-4">
        <div class="flex items-center justify-between">
            <h3 class="text-base font-semibold text-gray-900 dark:text-gray-100 flex items-center gap-2">
                <svg
                    class="w-5 h-5 text-indigo-600 dark:text-indigo-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
                Coherence Check
            </h3>
            {#if !result}
                <div class="flex items-center gap-2">
                    <button
                        type="button"
                        on:click={() => (showProviderSelect = !showProviderSelect)}
                        class="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
                    >
                        {showProviderSelect ? "Hide Options" : "Options"}
                    </button>
                    <button
                        on:click={checkCoherence}
                        disabled={loading}
                        class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 disabled:opacity-50"
                    >
                        {#if loading}
                            <span class="flex items-center gap-2">
                                <div
                                    class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"
                                ></div>
                                Checking...
                            </span>
                        {:else}
                            Check Coherence
                        {/if}
                    </button>
                </div>
            {:else}
                <button
                    on:click={() => (result = null)}
                    class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
                >
                    Clear
                </button>
            {/if}
        </div>

        {#if showProviderSelect && !result}
            <div class="bg-gray-50 dark:bg-gray-700 rounded-md p-3 border border-gray-200 dark:border-gray-600">
                <label
                    for="coherence-provider"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    LLM Provider for Analysis
                </label>
                <select
                    id="coherence-provider"
                    bind:value={selectedProvider}
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                >
                    <option value="openai">OpenAI (Recommended)</option>
                    <option value="anthropic">Anthropic (Claude)</option>
                    <option value="ollama">Ollama (Local)</option>
                </select>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Choose which AI provider to use for coherence analysis
                </p>
            </div>
        {/if}
    </div>

    {#if error}
        <div class="rounded-md bg-red-50 dark:bg-red-900/30 p-4 border border-red-200 dark:border-red-700">
            <p class="text-sm text-red-800 dark:text-red-300">{error}</p>
        </div>
    {/if}

    {#if result}
        <div class="space-y-4">
            <!-- Overall Status -->
            <div
                class="rounded-md p-4 border {result.coherent
                    ? 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700'
                    : 'bg-yellow-50 dark:bg-yellow-900/30 border-yellow-200 dark:border-yellow-700'}"
            >
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        {#if result.coherent}
                            <svg
                                class="h-5 w-5 text-green-600 dark:text-green-400"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                            >
                                <path
                                    fill-rule="evenodd"
                                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                    clip-rule="evenodd"
                                />
                            </svg>
                        {:else}
                            <svg
                                class="h-5 w-5 text-yellow-600 dark:text-yellow-400"
                                fill="currentColor"
                                viewBox="0 0 20 20"
                            >
                                <path
                                    fill-rule="evenodd"
                                    d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                                    clip-rule="evenodd"
                                />
                            </svg>
                        {/if}
                    </div>
                    <div class="ml-3 flex-1">
                        <h3
                            class="text-sm font-medium {result.coherent
                                ? 'text-green-800 dark:text-green-300'
                                : 'text-yellow-800 dark:text-yellow-300'}"
                        >
                            {result.coherent ? "Beat is coherent" : "Coherence issues detected"}
                        </h3>
                        <div
                            class="mt-2 text-sm {result.coherent
                                ? 'text-green-700 dark:text-green-300'
                                : 'text-yellow-700 dark:text-yellow-300'}"
                        >
                            <p>
                                {result.coherent
                                    ? "No significant issues found. The beat maintains narrative coherence."
                                    : `Found ${result.issues.length} issue${result.issues.length !== 1 ? "s" : ""} that may affect narrative coherence.`}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Issues List -->
            {#if result.issues.length > 0}
                <div class="space-y-3">
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Detected Issues
                    </h4>
                    {#each result.issues as issue}
                        <div class="rounded-md p-4 border {getSeverityColor(issue.severity)}">
                            <div class="flex items-start justify-between mb-2">
                                <div class="flex items-center gap-2">
                                    <span
                                        class="inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset uppercase {getSeverityBadge(
                                            issue.severity,
                                        )}"
                                    >
                                        {issue.severity}
                                    </span>
                                    <span class="text-sm font-medium">{formatIssueType(issue.type)}</span>
                                </div>
                            </div>
                            <p class="text-sm">{issue.description}</p>
                        </div>
                    {/each}
                </div>
            {/if}

            <!-- Suggestions -->
            {#if result.suggestions.length > 0}
                <div class="space-y-3">
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Suggestions for Improvement
                    </h4>
                    <div class="bg-indigo-50 dark:bg-indigo-900/30 rounded-md p-4 border border-indigo-200 dark:border-indigo-700">
                        <ul class="space-y-2 text-sm text-indigo-900 dark:text-indigo-200">
                            {#each result.suggestions as suggestion, i}
                                <li class="flex items-start gap-2">
                                    <span class="font-semibold">{i + 1}.</span>
                                    <span class="flex-1">{suggestion}</span>
                                </li>
                            {/each}
                        </ul>
                    </div>
                </div>
            {/if}

            <!-- Detailed Analysis (Collapsible) -->
            {#if result.analysis}
                <details bind:open={showAnalysis} class="mt-4">
                    <summary
                        class="text-sm font-medium text-gray-700 dark:text-gray-300 cursor-pointer hover:text-gray-900 dark:hover:text-gray-100 flex items-center gap-2"
                    >
                        <svg
                            class="w-4 h-4 transition-transform {showAnalysis ? 'rotate-90' : ''}"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                        >
                            <path
                                stroke-linecap="round"
                                stroke-linejoin="round"
                                stroke-width="2"
                                d="M9 5l7 7-7 7"
                            />
                        </svg>
                        Detailed Analysis
                    </summary>
                    <div
                        class="mt-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-md border border-gray-200 dark:border-gray-600"
                    >
                        <pre class="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">{result.analysis}</pre>
                    </div>
                </details>
            {/if}
        </div>
    {:else if !loading && !error}
        <p class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
            Click "Check Coherence" to analyze this beat for narrative consistency and coherence
            with the story and world context.
        </p>
    {/if}
</div>
