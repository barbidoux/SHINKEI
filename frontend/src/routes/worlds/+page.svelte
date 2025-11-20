<script lang="ts">
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import { auth } from "$lib/stores/auth";
    import { LoadingSpinner } from "$lib/components";

    interface World {
        id: string;
        name: string;
        overview: string;
        created_at: string;
    }

    let worlds: World[] = [];
    let loading = true;
    let error = "";

    onMount(async () => {
        if (!$auth.isAuthenticated) return;
        try {
            worlds = await api.get<World[]>("/worlds");
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    });
</script>

<div class="space-y-6">
    <div class="flex items-center justify-between">
        <h1 class="text-3xl font-bold tracking-tight text-gray-900">
            Your Worlds
        </h1>
        <a
            href="/worlds/new"
            class="rounded-md bg-indigo-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
            >Create World</a
        >
    </div>

    {#if loading}
        <div class="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" text="Loading worlds..." />
        </div>
    {:else if error}
        <div class="text-center py-12 text-red-500">{error}</div>
    {:else if worlds.length === 0}
        <div
            class="text-center py-12 bg-white rounded-lg shadow border border-gray-200"
        >
            <h3 class="mt-2 text-sm font-semibold text-gray-900">No worlds</h3>
            <p class="mt-1 text-sm text-gray-500">
                Get started by creating a new world.
            </p>
            <div class="mt-6">
                <a
                    href="/worlds/new"
                    class="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                >
                    <svg
                        class="-ml-0.5 mr-1.5 h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        aria-hidden="true"
                    >
                        <path
                            fill-rule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                            clip-rule="evenodd"
                        />
                    </svg>
                    Create World
                </a>
            </div>
        </div>
    {:else}
        <div class="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {#each worlds as world}
                <a
                    href="/worlds/{world.id}"
                    class="block hover:bg-gray-50 transition duration-150 ease-in-out"
                >
                    <div
                        class="overflow-hidden rounded-lg bg-white shadow border border-gray-200"
                    >
                        <div class="px-4 py-5 sm:p-6">
                            <h3
                                class="text-base font-semibold leading-6 text-gray-900"
                            >
                                {world.name}
                            </h3>
                            <p class="mt-1 text-sm text-gray-500 line-clamp-3">
                                {world.overview || "No overview provided."}
                            </p>
                            <div class="mt-4 text-xs text-gray-400">
                                Created {new Date(
                                    world.created_at,
                                ).toLocaleDateString()}
                            </div>
                        </div>
                    </div>
                </a>
            {/each}
        </div>
    {/if}
</div>
