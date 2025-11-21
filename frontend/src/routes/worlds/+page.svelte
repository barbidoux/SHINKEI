<script lang="ts">
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
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
    let importing = false;
    let importFileInput: HTMLInputElement;

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

    function handleImportClick() {
        importFileInput.click();
    }

    async function handleImportFile(event: Event) {
        const target = event.target as HTMLInputElement;
        const file = target.files?.[0];
        if (!file) return;

        importing = true;
        try {
            const fileContent = await file.text();
            const importData = JSON.parse(fileContent);

            // Import the world
            const newWorld = await api.post('/worlds/import', importData);

            alert('World imported successfully!');
            goto(`/worlds/${newWorld.id}`);
        } catch (e: any) {
            alert(`Failed to import world: ${e.message}`);
        } finally {
            importing = false;
            target.value = ''; // Reset file input
        }
    }
</script>

<input
    type="file"
    accept=".json"
    bind:this={importFileInput}
    on:change={handleImportFile}
    class="hidden"
/>

<div class="space-y-6">
    <div class="flex items-center justify-between">
        <h1 class="text-3xl font-bold tracking-tight text-gray-900 dark:text-gray-100">
            Your Worlds
        </h1>
        <div class="flex items-center gap-3">
            <button
                on:click={handleImportClick}
                disabled={importing}
                class="rounded-md bg-blue-600 dark:bg-blue-500 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 dark:hover:bg-blue-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 dark:focus-visible:outline-blue-400 disabled:opacity-50"
                title="Import world from JSON"
            >
                {importing ? 'Importing...' : 'Import World'}
            </button>
            <a
                href="/worlds/new"
                class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
                >Create World</a
            >
        </div>
    </div>

    {#if loading}
        <div class="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" text="Loading worlds..." />
        </div>
    {:else if error}
        <div class="text-center py-12 text-red-500 dark:text-red-400">{error}</div>
    {:else if worlds.length === 0}
        <div
            class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700"
        >
            <h3 class="mt-2 text-sm font-semibold text-gray-900 dark:text-gray-100">No worlds</h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Get started by creating a new world.
            </p>
            <div class="mt-6">
                <a
                    href="/worlds/new"
                    class="inline-flex items-center rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
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
                    class="block hover:bg-gray-50 dark:hover:bg-gray-800 transition duration-150 ease-in-out"
                >
                    <div
                        class="overflow-hidden rounded-lg bg-white dark:bg-gray-800 shadow border border-gray-200 dark:border-gray-700"
                    >
                        <div class="px-4 py-5 sm:p-6">
                            <h3
                                class="text-base font-semibold leading-6 text-gray-900 dark:text-gray-100"
                            >
                                {world.name}
                            </h3>
                            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400 line-clamp-3">
                                {world.overview || "No overview provided."}
                            </p>
                            <div class="mt-4 text-xs text-gray-400 dark:text-gray-500">
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
