<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";

    interface Story {
        id: string;
        title: string;
        synopsis: string;
        status: string;
        updated_at: string;
    }

    interface World {
        id: string;
        name: string;
        overview: string;
    }

    let world: World | null = null;
    let stories: Story[] = [];
    let loading = true;
    let error = "";

    $: worldId = $page.params.id;

    onMount(async () => {
        try {
            const [worldData, storiesData] = await Promise.all([
                api.get<World>(`/worlds/${worldId}`),
                api.get<Story[]>(`/worlds/${worldId}/stories`),
            ]);
            world = worldData;
            stories = storiesData;
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    });

    async function handleDeleteWorld() {
        if (
            !confirm(
                "Are you sure you want to delete this world? This will delete ALL stories, beats, and events in this world. This action cannot be undone.",
            )
        ) {
            return;
        }

        try {
            await api.delete(`/worlds/${worldId}`);
            goto("/worlds");
        } catch (e: any) {
            alert(`Failed to delete world: ${e.message}`);
        }
    }
</script>

{#if loading}
    <div class="text-center py-12">Loading world details...</div>
{:else if error}
    <div class="text-center py-12 text-red-500">{error}</div>
{:else if world}
    <div class="space-y-8">
        <div class="border-b border-gray-200 pb-5">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold leading-6 text-gray-900">
                        {world.name}
                    </h1>
                    <p class="mt-2 max-w-4xl text-sm text-gray-500">
                        {world.overview || "No overview provided."}
                    </p>
                </div>
                <div class="flex items-center gap-3">
                    <a
                        href="/worlds/{worldId}/events"
                        class="inline-flex items-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500"
                    >
                        View Events
                    </a>
                    <a
                        href="/worlds/{worldId}/edit"
                        class="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                    >
                        Edit
                    </a>
                    <button
                        on:click={handleDeleteWorld}
                        class="inline-flex items-center rounded-md bg-red-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500"
                    >
                        Delete
                    </button>
                </div>
            </div>
        </div>

        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold text-gray-900">Stories</h2>
                <a
                    href="/worlds/{worldId}/stories/new"
                    class="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                    >New Story</a
                >
            </div>

            {#if stories.length === 0}
                <div
                    class="text-center py-12 bg-white rounded-lg shadow border border-gray-200"
                >
                    <p class="text-sm text-gray-500">No stories yet.</p>
                </div>
            {:else}
                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {#each stories as story}
                        <a
                            href="/stories/{story.id}"
                            class="block hover:bg-gray-50 transition duration-150 ease-in-out"
                        >
                            <div
                                class="relative flex items-center space-x-3 rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500 focus-within:ring-offset-2 hover:border-gray-400"
                            >
                                <div class="min-w-0 flex-1">
                                    <div class="focus:outline-none">
                                        <span
                                            class="absolute inset-0"
                                            aria-hidden="true"
                                        ></span>
                                        <p
                                            class="text-sm font-medium text-gray-900"
                                        >
                                            {story.title}
                                        </p>
                                        <p
                                            class="truncate text-sm text-gray-500"
                                        >
                                            {story.synopsis || "No synopsis"}
                                        </p>
                                    </div>
                                </div>
                                <div
                                    class="flex-shrink-0 whitespace-nowrap text-sm text-gray-500"
                                >
                                    <span
                                        class="inline-flex items-center rounded-full bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20"
                                        >{story.status}</span
                                    >
                                </div>
                            </div>
                        </a>
                    {/each}
                </div>
            {/if}
        </div>
    </div>
{/if}
