<script lang="ts">
    import { api } from "$lib/api";

    export let storyId: string;

    interface CoherenceIssue {
        type: string;
        severity: "low" | "medium" | "high";
        description: string;
        beat_range?: string;
    }

    interface CharacterArc {
        name: string;
        arc_status: string;
    }

    interface PlotThread {
        name: string;
        status: string;
        description: string;
    }

    interface TimelineIssue {
        beat_range: string;
        description: string;
    }

    interface StoryCoherenceResult {
        coherent: boolean;
        issues: CoherenceIssue[];
        suggestions: string[];
        character_arcs: CharacterArc[];
        plot_threads: PlotThread[];
        timeline_issues: TimelineIssue[];
        analysis?: string;
    }

    let loading = false;
    let error = "";
    let result: StoryCoherenceResult | null = null;
    let showAnalysis = false;
    let showProviderSelect = false;
    let showRangeSelect = false;
    let selectedProvider: "openai" | "anthropic" | "ollama" = "openai";
    let startBeatIndex: number | null = null;
    let endBeatIndex: number | null = null;

    async function checkStoryCoherence() {
        loading = true;
        error = "";
        result = null;

        try {
            const body: any = {
                provider: selectedProvider
            };

            if (startBeatIndex !== null && startBeatIndex > 0) {
                body.start_beat_index = startBeatIndex;
            }

            if (endBeatIndex !== null && endBeatIndex > 0) {
                body.end_beat_index = endBeatIndex;
            }

            result = await api.post<StoryCoherenceResult>(
                `/narrative/stories/${storyId}/check-coherence`,
                body
            );

            // Auto-expand analysis when story is coherent (no issues to review first)
            showAnalysis = result?.coherent ?? false;
        } catch (e: any) {
            error = e.message || "Failed to check story coherence";
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

    function getPlotThreadStatusColor(status: string): string {
        const lowerStatus = status.toLowerCase();
        if (lowerStatus.includes("ongoing") || lowerStatus.includes("active")) {
            return "bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-300";
        } else if (lowerStatus.includes("resolved") || lowerStatus.includes("completed")) {
            return "bg-green-100 dark:bg-green-900/50 text-green-800 dark:text-green-300";
        } else if (lowerStatus.includes("unresolved") || lowerStatus.includes("abandoned")) {
            return "bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-300";
        }
        return "bg-purple-100 dark:bg-purple-900/50 text-purple-800 dark:text-purple-300";
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
                    class="w-5 h-5 text-purple-600 dark:text-purple-400"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                </svg>
                Story Coherence Check
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
                        on:click={checkStoryCoherence}
                        disabled={loading}
                        class="rounded-md bg-purple-600 dark:bg-purple-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 dark:hover:bg-purple-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600 dark:focus-visible:outline-purple-400 disabled:opacity-50"
                    >
                        {#if loading}
                            <span class="flex items-center gap-2">
                                <div
                                    class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"
                                ></div>
                                Analyzing...
                            </span>
                        {:else}
                            Check Story Coherence
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
            <div class="bg-gray-50 dark:bg-gray-700 rounded-md p-3 border border-gray-200 dark:border-gray-600 space-y-3">
                <div>
                    <label
                        for="story-coherence-provider"
                        class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                    >
                        LLM Provider for Analysis
                    </label>
                    <select
                        id="story-coherence-provider"
                        bind:value={selectedProvider}
                        class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-purple-500 dark:focus:ring-purple-400 sm:text-sm"
                    >
                        <option value="openai">OpenAI (Recommended)</option>
                        <option value="anthropic">Anthropic (Claude)</option>
                        <option value="ollama">Ollama (Local)</option>
                    </select>
                    <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Choose which AI provider to use for coherence analysis
                    </p>
                </div>

                <div>
                    <button
                        type="button"
                        on:click={() => (showRangeSelect = !showRangeSelect)}
                        class="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-800 dark:hover:text-purple-300 flex items-center gap-1"
                    >
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                        {showRangeSelect ? "Hide Range Options" : "Analyze Specific Beat Range"}
                    </button>
                </div>

                {#if showRangeSelect}
                    <div class="bg-white dark:bg-gray-800 rounded-md p-3 border border-purple-200 dark:border-purple-700 space-y-3">
                        <p class="text-xs text-gray-600 dark:text-gray-400">
                            Leave empty to analyze the entire story. Specify a range to focus on specific beats.
                        </p>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label
                                    for="start-beat-index"
                                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                >
                                    Start Beat (optional)
                                </label>
                                <input
                                    id="start-beat-index"
                                    type="number"
                                    min="1"
                                    bind:value={startBeatIndex}
                                    placeholder="1"
                                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-purple-500 dark:focus:ring-purple-400 sm:text-sm"
                                />
                            </div>
                            <div>
                                <label
                                    for="end-beat-index"
                                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1"
                                >
                                    End Beat (optional)
                                </label>
                                <input
                                    id="end-beat-index"
                                    type="number"
                                    min="1"
                                    bind:value={endBeatIndex}
                                    placeholder="Last beat"
                                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-purple-500 dark:focus:ring-purple-400 sm:text-sm"
                                />
                            </div>
                        </div>
                    </div>
                {/if}
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
                            {result.coherent ? "Story is coherent" : "Coherence issues detected"}
                        </h3>
                        <div
                            class="mt-2 text-sm {result.coherent
                                ? 'text-green-700 dark:text-green-300'
                                : 'text-yellow-700 dark:text-yellow-300'}"
                        >
                            <p>
                                {result.coherent
                                    ? "No significant issues found. The story maintains narrative coherence across beats."
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
                                <div class="flex items-center gap-2 flex-wrap">
                                    <span
                                        class="inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset uppercase {getSeverityBadge(
                                            issue.severity,
                                        )}"
                                    >
                                        {issue.severity}
                                    </span>
                                    <span class="text-sm font-medium">{formatIssueType(issue.type)}</span>
                                    {#if issue.beat_range}
                                        <span class="inline-flex items-center rounded-md bg-gray-100 dark:bg-gray-700 px-2 py-1 text-xs text-gray-600 dark:text-gray-400">
                                            Beats: {issue.beat_range}
                                        </span>
                                    {/if}
                                </div>
                            </div>
                            <p class="text-sm">{issue.description}</p>
                        </div>
                    {/each}
                </div>
            {/if}

            <!-- Character Arcs -->
            {#if result.character_arcs && result.character_arcs.length > 0}
                <div class="space-y-3">
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <svg class="w-4 h-4 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        Character Arcs
                    </h4>
                    <div class="bg-purple-50 dark:bg-purple-900/30 rounded-md p-4 border border-purple-200 dark:border-purple-700">
                        <div class="space-y-2">
                            {#each result.character_arcs as arc}
                                <div class="flex items-start gap-2">
                                    <span class="font-semibold text-sm text-purple-900 dark:text-purple-200">{arc.name}:</span>
                                    <span class="text-sm text-purple-800 dark:text-purple-300">{arc.arc_status}</span>
                                </div>
                            {/each}
                        </div>
                    </div>
                </div>
            {/if}

            <!-- Plot Threads -->
            {#if result.plot_threads && result.plot_threads.length > 0}
                <div class="space-y-3">
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <svg class="w-4 h-4 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Plot Threads
                    </h4>
                    <div class="space-y-2">
                        {#each result.plot_threads as thread}
                            <div class="bg-white dark:bg-gray-800 rounded-md p-3 border border-gray-200 dark:border-gray-600">
                                <div class="flex items-center gap-2 mb-2">
                                    <span class="font-semibold text-sm text-gray-900 dark:text-gray-100">{thread.name}</span>
                                    <span class="inline-flex items-center rounded-md px-2 py-1 text-xs font-medium {getPlotThreadStatusColor(thread.status)}">
                                        {thread.status}
                                    </span>
                                </div>
                                <p class="text-sm text-gray-700 dark:text-gray-300">{thread.description}</p>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}

            <!-- Timeline Issues -->
            {#if result.timeline_issues && result.timeline_issues.length > 0}
                <div class="space-y-3">
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        <svg class="w-4 h-4 text-orange-600 dark:text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Timeline Consistency
                    </h4>
                    <div class="space-y-2">
                        {#each result.timeline_issues as timelineIssue}
                            <div class="bg-orange-50 dark:bg-orange-900/30 rounded-md p-3 border border-orange-200 dark:border-orange-700">
                                <div class="flex items-start gap-2">
                                    <span class="inline-flex items-center rounded-md bg-orange-100 dark:bg-orange-900/50 px-2 py-1 text-xs font-medium text-orange-800 dark:text-orange-300">
                                        Beats: {timelineIssue.beat_range}
                                    </span>
                                    <p class="text-sm text-orange-800 dark:text-orange-300 flex-1">{timelineIssue.description}</p>
                                </div>
                            </div>
                        {/each}
                    </div>
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
                <div class="mt-4">
                    {#if result.coherent}
                        <div class="mb-2 text-sm text-gray-600 dark:text-gray-400 bg-purple-50 dark:bg-purple-900/20 px-3 py-2 rounded-md border border-purple-200 dark:border-purple-700">
                            Full AI analysis report shown below. Review to understand the coherence assessment.
                        </div>
                    {/if}
                    <details bind:open={showAnalysis}>
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
                            {result.coherent ? "Full Analysis Report" : "Detailed Analysis"}
                        </summary>
                        <div
                            class="mt-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-md border border-gray-200 dark:border-gray-600"
                        >
                            <pre class="text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono">{result.analysis}</pre>
                        </div>
                    </details>
                </div>
            {/if}
        </div>
    {:else if !loading && !error}
        <p class="text-sm text-gray-500 dark:text-gray-400 text-center py-4">
            Click "Check Story Coherence" to analyze narrative consistency across the entire story or
            a specific range of beats. This comprehensive check examines timeline consistency, character
            arcs, plot threads, world law adherence, and overall narrative flow.
        </p>
    {/if}
</div>
