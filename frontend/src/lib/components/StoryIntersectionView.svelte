<script lang="ts">
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import type { StoryBeat, StoryResponse } from "$lib/types";

    export let eventId: string;
    export let eventSummary: string = "";
    export let onClose: (() => void) | null = null;

    interface BeatWithStory extends StoryBeat {
        story: StoryResponse;
    }

    interface StoryGroup {
        story: StoryResponse;
        beats: BeatWithStory[];
    }

    let loading = true;
    let error = "";
    let storyGroups: StoryGroup[] = [];

    onMount(async () => {
        await loadIntersectionData();
    });

    async function loadIntersectionData() {
        loading = true;
        error = "";

        try {
            const beats = await api.get<BeatWithStory[]>(
                `/events/${eventId}/beats`,
            );

            // Group beats by story
            const grouped = new Map<string, StoryGroup>();

            for (const beat of beats) {
                if (!grouped.has(beat.story_id)) {
                    grouped.set(beat.story_id, {
                        story: beat.story,
                        beats: [],
                    });
                }
                grouped.get(beat.story_id)!.beats.push(beat);
            }

            // Convert to array and sort by story title
            storyGroups = Array.from(grouped.values()).sort((a, b) =>
                a.story.title.localeCompare(b.story.title),
            );
        } catch (e: any) {
            error = e.message || "Failed to load story intersection data";
        } finally {
            loading = false;
        }
    }

    function getStoryModeLabel(mode: string): string {
        const labels: Record<string, string> = {
            autonomous: "Autonomous",
            collaborative: "Collaborative",
            manual: "Manual",
        };
        return labels[mode] || mode;
    }
</script>

<div class="story-intersection-view">
    <!-- Header -->
    <div class="border-b border-gray-200 pb-4 mb-6">
        <div class="flex items-start justify-between">
            <div class="flex-1">
                <h2 class="text-2xl font-bold text-gray-900">
                    Story Intersection
                </h2>
                {#if eventSummary}
                    <p class="mt-2 text-sm text-gray-600">
                        Event: <span class="font-medium">{eventSummary}</span>
                    </p>
                {/if}
                <p class="mt-1 text-xs text-gray-500">
                    All story beats occurring at this canonical world event
                </p>
            </div>
            {#if onClose}
                <button
                    on:click={onClose}
                    class="text-gray-400 hover:text-gray-500"
                >
                    <svg
                        class="h-6 w-6"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M6 18L18 6M6 6l12 12"
                        />
                    </svg>
                </button>
            {/if}
        </div>
    </div>

    <!-- Content -->
    {#if loading}
        <div class="text-center py-12">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            <p class="mt-2 text-sm text-gray-500">Loading story intersections...</p>
        </div>
    {:else if error}
        <div class="text-center py-12">
            <div class="text-red-500 mb-2">
                <svg
                    class="h-12 w-12 mx-auto"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                >
                    <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        stroke-width="2"
                        d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
            </div>
            <p class="text-sm text-red-600">{error}</p>
        </div>
    {:else if storyGroups.length === 0}
        <div
            class="text-center py-12 bg-gray-50 rounded-lg border border-gray-200"
        >
            <p class="text-sm text-gray-500">
                No story beats are linked to this event yet.
            </p>
            <p class="mt-1 text-xs text-gray-400">
                Create beats in your stories and link them to this world event
                to see the intersection.
            </p>
        </div>
    {:else}
        <div class="space-y-6">
            <!-- Summary Stats -->
            <div class="bg-indigo-50 rounded-lg p-4 border border-indigo-100">
                <div class="flex items-center gap-6 text-sm">
                    <div>
                        <span class="font-semibold text-indigo-900"
                            >{storyGroups.length}</span
                        >
                        <span class="text-indigo-700 ml-1"
                            >{storyGroups.length === 1
                                ? "Story"
                                : "Stories"}</span
                        >
                    </div>
                    <div>
                        <span class="font-semibold text-indigo-900"
                            >{storyGroups.reduce(
                                (sum, g) => sum + g.beats.length,
                                0,
                            )}</span
                        >
                        <span class="text-indigo-700 ml-1">Total Beats</span>
                    </div>
                </div>
            </div>

            <!-- Story Groups -->
            {#each storyGroups as group}
                <div
                    class="bg-white rounded-lg border border-gray-300 shadow-sm overflow-hidden"
                >
                    <!-- Story Header -->
                    <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
                        <div class="flex items-start justify-between">
                            <div>
                                <h3 class="text-lg font-semibold text-gray-900">
                                    {group.story.title}
                                </h3>
                                {#if group.story.synopsis}
                                    <p class="mt-1 text-sm text-gray-600">
                                        {group.story.synopsis}
                                    </p>
                                {/if}
                            </div>
                            <div class="flex items-center gap-2">
                                <span
                                    class="inline-flex items-center rounded-md bg-purple-50 px-2 py-1 text-xs font-medium text-purple-700 ring-1 ring-inset ring-purple-600/20"
                                >
                                    {getStoryModeLabel(group.story.mode || "manual")}
                                </span>
                                <span
                                    class="inline-flex items-center rounded-md bg-gray-100 px-2 py-1 text-xs font-medium text-gray-600"
                                >
                                    {group.beats.length}
                                    {group.beats.length === 1 ? "beat" : "beats"}
                                </span>
                            </div>
                        </div>
                    </div>

                    <!-- Story Beats -->
                    <div class="divide-y divide-gray-200">
                        {#each group.beats as beat}
                            <div class="px-6 py-4 hover:bg-gray-50">
                                <div class="flex items-start justify-between mb-2">
                                    <div class="flex items-center gap-2">
                                        <span
                                            class="inline-flex items-center rounded-md bg-indigo-50 px-2 py-1 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-600/20"
                                        >
                                            {beat.type}
                                        </span>
                                        {#if beat.local_time_label}
                                            <span
                                                class="text-xs text-gray-500"
                                            >
                                                {beat.local_time_label}
                                            </span>
                                        {/if}
                                        {#if beat.summary}
                                            <span
                                                class="text-xs font-medium text-gray-700"
                                            >
                                                {beat.summary}
                                            </span>
                                        {/if}
                                    </div>
                                    <a
                                        href="/stories/{group.story.id}/beats/{beat.id}/edit"
                                        class="text-xs text-indigo-600 hover:text-indigo-500"
                                    >
                                        View →
                                    </a>
                                </div>
                                <div
                                    class="prose prose-sm max-w-none text-gray-700"
                                >
                                    <div class="line-clamp-3">
                                        {beat.content}
                                    </div>
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .story-intersection-view {
        width: 100%;
    }

    .line-clamp-3 {
        display: -webkit-box;
        -webkit-line-clamp: 3;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    .prose {
        color: inherit;
    }

    .prose p {
        margin: 0;
    }
</style>
