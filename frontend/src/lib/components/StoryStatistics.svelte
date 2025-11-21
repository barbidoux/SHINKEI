<script lang="ts">
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import type { StoryStatistics } from "$lib/types";

    export let storyId: string;

    let stats: StoryStatistics | null = null;
    let loading = true;
    let error = "";

    onMount(async () => {
        try {
            stats = await api.get<StoryStatistics>(`/stories/${storyId}/statistics`);
            loading = false;
        } catch (e: any) {
            error = e.message || "Failed to load statistics";
            loading = false;
        }
    });

    function formatNumber(num: number): string {
        return new Intl.NumberFormat().format(num);
    }

    function getPercentage(value: number, total: number): number {
        if (total === 0) return 0;
        return Math.round((value / total) * 100);
    }

    $: totalBeats = stats?.beat_count || 0;
    $: aiBeats = stats?.ai_generated_count || 0;
    $: userBeats = stats?.user_generated_count || 0;
    $: collaborativeBeats = stats?.collaborative_count || 0;
</script>

{#if loading}
    <div class="flex items-center justify-center py-12">
        <div class="text-center">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 dark:border-indigo-400"></div>
            <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">Loading statistics...</p>
        </div>
    </div>
{:else if error}
    <div class="rounded-md bg-red-50 dark:bg-red-900/30 p-4 border border-red-200 dark:border-red-700">
        <p class="text-sm text-red-800 dark:text-red-300">{error}</p>
    </div>
{:else if stats}
    <div class="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
        <div class="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Story Statistics
            </h3>
        </div>

        <div class="p-6 space-y-6">
            <!-- Key Metrics Grid -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <!-- Beat Count -->
                <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        Total Beats
                    </dt>
                    <dd class="mt-1 text-3xl font-semibold text-gray-900 dark:text-gray-100">
                        {formatNumber(stats.beat_count)}
                    </dd>
                </div>

                <!-- Word Count -->
                <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        Word Count
                    </dt>
                    <dd class="mt-1 text-3xl font-semibold text-gray-900 dark:text-gray-100">
                        {formatNumber(stats.word_count)}
                    </dd>
                </div>

                <!-- Reading Time -->
                <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        Reading Time
                    </dt>
                    <dd class="mt-1 text-3xl font-semibold text-gray-900 dark:text-gray-100">
                        {stats.estimated_reading_minutes}<span class="text-lg ml-1 text-gray-500">min</span>
                    </dd>
                </div>

                <!-- Event Links -->
                <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
                    <dt class="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                        Event Links
                    </dt>
                    <dd class="mt-1 text-3xl font-semibold text-gray-900 dark:text-gray-100">
                        {formatNumber(stats.world_event_links)}
                    </dd>
                </div>
            </div>

            <!-- Authoring Breakdown -->
            <div>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                    Authoring Distribution
                </h4>
                <div class="space-y-3">
                    <!-- AI Generated -->
                    <div>
                        <div class="flex items-center justify-between text-sm mb-1">
                            <span class="text-gray-600 dark:text-gray-300">AI Generated</span>
                            <span class="font-medium text-gray-900 dark:text-gray-100">
                                {aiBeats} ({getPercentage(aiBeats, totalBeats)}%)
                            </span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                                class="bg-purple-600 dark:bg-purple-500 h-2 rounded-full transition-all"
                                style="width: {getPercentage(aiBeats, totalBeats)}%"
                            ></div>
                        </div>
                    </div>

                    <!-- Collaborative -->
                    <div>
                        <div class="flex items-center justify-between text-sm mb-1">
                            <span class="text-gray-600 dark:text-gray-300">Collaborative</span>
                            <span class="font-medium text-gray-900 dark:text-gray-100">
                                {collaborativeBeats} ({getPercentage(collaborativeBeats, totalBeats)}%)
                            </span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                                class="bg-indigo-600 dark:bg-indigo-500 h-2 rounded-full transition-all"
                                style="width: {getPercentage(collaborativeBeats, totalBeats)}%"
                            ></div>
                        </div>
                    </div>

                    <!-- User Written -->
                    <div>
                        <div class="flex items-center justify-between text-sm mb-1">
                            <span class="text-gray-600 dark:text-gray-300">User Written</span>
                            <span class="font-medium text-gray-900 dark:text-gray-100">
                                {userBeats} ({getPercentage(userBeats, totalBeats)}%)
                            </span>
                        </div>
                        <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                                class="bg-green-600 dark:bg-green-500 h-2 rounded-full transition-all"
                                style="width: {getPercentage(userBeats, totalBeats)}%"
                            ></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Beat Type Distribution -->
            {#if Object.keys(stats.beat_type_distribution).length > 0}
                <div>
                    <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
                        Beat Type Distribution
                    </h4>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
                        {#each Object.entries(stats.beat_type_distribution) as [type, count]}
                            <div class="bg-gray-50 dark:bg-gray-900 rounded-lg p-3">
                                <div class="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                                    {type.replace('_', ' ')}
                                </div>
                                <div class="mt-1 text-2xl font-semibold text-gray-900 dark:text-gray-100">
                                    {count}
                                </div>
                            </div>
                        {/each}
                    </div>
                </div>
            {/if}

            <!-- Additional Details -->
            <div class="border-t border-gray-200 dark:border-gray-700 pt-4">
                <dl class="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-3 text-sm">
                    <div class="flex justify-between">
                        <dt class="text-gray-500 dark:text-gray-400">Character Count:</dt>
                        <dd class="font-medium text-gray-900 dark:text-gray-100">
                            {formatNumber(stats.character_count)}
                        </dd>
                    </div>
                    {#if stats.latest_beat_date}
                        <div class="flex justify-between">
                            <dt class="text-gray-500 dark:text-gray-400">Last Beat:</dt>
                            <dd class="font-medium text-gray-900 dark:text-gray-100">
                                {new Date(stats.latest_beat_date).toLocaleDateString()}
                            </dd>
                        </div>
                    {/if}
                </dl>
            </div>
        </div>
    </div>
{/if}
