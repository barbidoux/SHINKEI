<script lang="ts">
    import { api } from "$lib/api";
    import { onMount } from "svelte";
    import type { BeatModificationHistoryResponse, BeatModificationResponse } from "$lib/types/beat";

    export let storyId: string;
    export let beatId: string;
    export let onViewModification: (modification: BeatModificationResponse) => void;

    let loading = true;
    let error = "";
    let history: BeatModificationHistoryResponse | null = null;

    onMount(async () => {
        await loadHistory();
    });

    async function loadHistory() {
        loading = true;
        error = "";

        try {
            const response = await api.get<BeatModificationHistoryResponse>(
                `/narrative/stories/${storyId}/beats/${beatId}/modifications`
            );
            history = response;
        } catch (e: any) {
            error = e.message || "Failed to load modification history";
        } finally {
            loading = false;
        }
    }

    function formatDate(dateString: string): string {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;

        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;

        const diffDays = Math.floor(diffHours / 24);
        if (diffDays < 7) return `${diffDays}d ago`;

        return date.toLocaleDateString();
    }

    function truncate(text: string, length: number = 100): string {
        return text.length > length ? text.substring(0, length) + "..." : text;
    }
</script>

<div class="modification-history">
    <div class="px-4 py-3 bg-gray-50 border-b border-gray-200">
        <h4 class="text-sm font-medium text-gray-900">Modification History</h4>
        <p class="text-xs text-gray-500 mt-1">
            Recent changes to this beat
        </p>
    </div>

    <div class="divide-y divide-gray-200">
        {#if loading}
            <div class="px-4 py-8 text-center">
                <div class="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
                <p class="text-sm text-gray-500 mt-2">Loading history...</p>
            </div>
        {:else if error}
            <div class="px-4 py-4 bg-red-50">
                <p class="text-sm text-red-800">{error}</p>
            </div>
        {:else if !history || history.modifications.length === 0}
            <div class="px-4 py-8 text-center">
                <svg
                    class="mx-auto h-12 w-12 text-gray-400"
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
                <p class="mt-2 text-sm text-gray-500">No modification history yet</p>
                <p class="text-xs text-gray-400 mt-1">
                    Previous modifications will appear here
                </p>
            </div>
        {:else}
            {#each history.modifications as modification}
                <div class="px-4 py-3 hover:bg-gray-50 transition-colors cursor-pointer"
                     on:click={() => onViewModification(modification)}
                     on:keydown={(e) => e.key === "Enter" && onViewModification(modification)}
                     role="button"
                     tabindex="0">
                    <div class="flex items-start justify-between">
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2 mb-1">
                                {#if modification.applied}
                                    <span
                                        class="inline-flex items-center rounded-md bg-green-50 px-2 py-0.5 text-xs font-medium text-green-700"
                                    >
                                        Applied
                                    </span>
                                {:else}
                                    <span
                                        class="inline-flex items-center rounded-md bg-gray-50 px-2 py-0.5 text-xs font-medium text-gray-600"
                                    >
                                        Proposed
                                    </span>
                                {/if}
                                <span class="text-xs text-gray-500">
                                    {formatDate(modification.created_at)}
                                </span>
                            </div>
                            <p class="text-sm text-gray-900 font-medium truncate">
                                {truncate(modification.modification_instructions, 80)}
                            </p>
                            {#if modification.reasoning}
                                <p class="text-xs text-gray-600 mt-1">
                                    {truncate(modification.reasoning, 120)}
                                </p>
                            {/if}
                        </div>
                        <div class="ml-2 flex-shrink-0">
                            <svg
                                class="h-5 w-5 text-gray-400"
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
                        </div>
                    </div>
                </div>
            {/each}
        {/if}
    </div>

    {#if history && history.total > 0}
        <div class="px-4 py-2 bg-gray-50 border-t border-gray-200 text-center">
            <p class="text-xs text-gray-500">
                Showing {history.modifications.length} of {history.total} modification{history.total !== 1 ? "s" : ""}
            </p>
        </div>
    {/if}
</div>

<style>
    .modification-history {
        background: white;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        overflow: hidden;
    }
</style>
