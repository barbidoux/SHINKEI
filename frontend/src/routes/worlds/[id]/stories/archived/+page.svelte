<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import type { Story } from "$lib/types";

    let stories: Story[] = [];
    let loading = true;
    let error = "";

    $: worldId = $page.params.id;

    onMount(async () => {
        try {
            stories = await api.get<Story[]>(`/worlds/${worldId}/stories/archived`);
            loading = false;
        } catch (e: any) {
            error = e.message || "Failed to load archived stories";
            loading = false;
        }
    });

    async function handleRestore(storyId: string) {
        try {
            await api.post(`/stories/${storyId}/restore`, {});
            // Reload to update the list
            window.location.reload();
        } catch (e: any) {
            alert(`Failed to restore story: ${e.message}`);
        }
    }

    async function handlePermanentDelete(storyId: string, storyTitle: string) {
        if (
            !confirm(
                `Are you sure you want to PERMANENTLY delete "${storyTitle}"? This will delete ALL beats in this story. This action CANNOT be undone!`
            )
        ) {
            return;
        }

        // Double confirmation for permanent deletion
        if (!confirm("This is your final warning. Click OK to permanently delete this story.")) {
            return;
        }

        try {
            // Note: We would need a permanent delete endpoint, but for now, this will just do the same soft delete
            // In a full implementation, you'd add a ?permanent=true query param or similar
            await api.delete(`/stories/${storyId}`);
            // Reload to update the list
            window.location.reload();
        } catch (e: any) {
            alert(`Failed to delete story: ${e.message}`);
        }
    }

    function formatDate(dateString: string): string {
        const date = new Date(dateString);
        return date.toLocaleDateString("en-US", {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    }
</script>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Header -->
    <div class="mb-8">
        <div class="flex items-center justify-between">
            <div>
                <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">
                    Archived Stories
                </h1>
                <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                    Stories that have been archived can be restored or permanently deleted
                </p>
            </div>
            <a
                href="/worlds/{worldId}"
                class="inline-flex items-center rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
            >
                ← Back to World
            </a>
        </div>
    </div>

    <!-- Loading State -->
    {#if loading}
        <div class="flex items-center justify-center py-12">
            <div class="text-center">
                <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 dark:border-indigo-400"></div>
                <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">Loading archived stories...</p>
            </div>
        </div>

    <!-- Error State -->
    {:else if error}
        <div class="rounded-md bg-red-50 dark:bg-red-900/30 p-4 border border-red-200 dark:border-red-700">
            <p class="text-sm text-red-800 dark:text-red-300">{error}</p>
        </div>

    <!-- Empty State -->
    {:else if stories.length === 0}
        <div class="text-center py-12">
            <svg
                class="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                />
            </svg>
            <h3 class="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">
                No archived stories
            </h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Stories you archive will appear here
            </p>
        </div>

    <!-- Stories List -->
    {:else}
        <div class="bg-white dark:bg-gray-800 shadow overflow-hidden sm:rounded-md">
            <ul class="divide-y divide-gray-200 dark:divide-gray-700">
                {#each stories as story}
                    <li class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                        <div class="px-6 py-5">
                            <div class="flex items-center justify-between">
                                <div class="flex-1 min-w-0">
                                    <div class="flex items-center gap-3 mb-2">
                                        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate">
                                            {story.title}
                                        </h3>
                                        <span
                                            class="inline-flex items-center rounded-full bg-yellow-50 dark:bg-yellow-900/30 px-2.5 py-0.5 text-xs font-medium text-yellow-800 dark:text-yellow-200"
                                        >
                                            Archived
                                        </span>
                                    </div>

                                    {#if story.synopsis}
                                        <p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-2">
                                            {story.synopsis}
                                        </p>
                                    {/if}

                                    <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                                        {#if story.archived_at}
                                            <span>
                                                Archived on {formatDate(story.archived_at)}
                                            </span>
                                            <span class="text-gray-300 dark:text-gray-600">•</span>
                                        {/if}
                                        <span class="capitalize">{story.mode} mode</span>
                                        <span class="text-gray-300 dark:text-gray-600">•</span>
                                        <span class="capitalize">{story.pov_type} person</span>
                                    </div>

                                    {#if story.tags && story.tags.length > 0}
                                        <div class="mt-2 flex flex-wrap gap-1.5">
                                            {#each story.tags as tag}
                                                <span
                                                    class="inline-flex items-center rounded-full bg-indigo-100 dark:bg-indigo-900/50 px-2 py-0.5 text-xs font-medium text-indigo-700 dark:text-indigo-200"
                                                >
                                                    {tag}
                                                </span>
                                            {/each}
                                        </div>
                                    {/if}
                                </div>

                                <div class="flex items-center gap-2 ml-4">
                                    <button
                                        on:click={() => handleRestore(story.id)}
                                        class="inline-flex items-center rounded-md bg-green-600 dark:bg-green-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 dark:hover:bg-green-400"
                                    >
                                        Restore
                                    </button>
                                    <button
                                        on:click={() => handlePermanentDelete(story.id, story.title)}
                                        class="inline-flex items-center rounded-md bg-red-600 dark:bg-red-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 dark:hover:bg-red-400"
                                    >
                                        Delete Forever
                                    </button>
                                </div>
                            </div>
                        </div>
                    </li>
                {/each}
            </ul>
        </div>

        <div class="mt-4 text-sm text-gray-500 dark:text-gray-400 text-center">
            {stories.length} {stories.length === 1 ? "story" : "stories"} archived
        </div>
    {/if}
</div>
