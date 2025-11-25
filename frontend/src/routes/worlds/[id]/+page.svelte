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

    interface Character {
        id: string;
        name: string;
        role?: string;
        importance: string;
    }

    interface Location {
        id: string;
        name: string;
        location_type?: string;
        parent_location_id?: string;
    }

    let world: World | null = null;
    let stories: Story[] = [];
    let characters: Character[] = [];
    let locations: Location[] = [];
    let loading = true;
    let error = "";

    $: worldId = $page.params.id;

    onMount(async () => {
        try {
            const [worldData, storiesData, charactersData, locationsData] = await Promise.all([
                api.get<World>(`/worlds/${worldId}`),
                api.get<Story[]>(`/worlds/${worldId}/stories`),
                api.get<{ characters: Character[]; total: number }>(`/worlds/${worldId}/characters?limit=5`),
                api.get<{ locations: Location[]; total: number }>(`/worlds/${worldId}/locations?limit=5`),
            ]);
            world = worldData;
            stories = storiesData;
            characters = charactersData.characters;
            locations = locationsData.locations;
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

    async function handleExportWorld() {
        try {
            const response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/worlds/${worldId}/export`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`,
                }
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            const exportData = await response.json();

            // Create download
            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${world?.name.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_export_${Date.now()}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (e: any) {
            alert(`Failed to export world: ${e.message}`);
        }
    }

    let importFileInput: HTMLInputElement;
    let importing = false;
    let duplicating = false;

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

    async function handleDuplicateWorld() {
        if (!confirm(`Duplicate "${world?.name}"? This will create a complete copy with all events, stories, and story beats.`)) {
            return;
        }

        duplicating = true;
        try {
            const newWorld = await api.post(`/worlds/${worldId}/duplicate`, {});
            alert('World duplicated successfully!');
            goto(`/worlds/${newWorld.id}`);
        } catch (e: any) {
            alert(`Failed to duplicate world: ${e.message}`);
        } finally {
            duplicating = false;
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

{#if loading}
    <div class="text-center py-12 text-gray-600 dark:text-gray-400">Loading world details...</div>
{:else if error}
    <div class="text-center py-12 text-red-500 dark:text-red-400">{error}</div>
{:else if world}
    <div class="space-y-8">
        <div class="border-b border-gray-200 dark:border-gray-700 pb-5">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold leading-6 text-gray-900 dark:text-gray-100">
                        {world.name}
                    </h1>
                    <p class="mt-2 max-w-4xl text-sm text-gray-500 dark:text-gray-400">
                        {world.overview || "No overview provided."}
                    </p>
                </div>
                <div class="flex items-center gap-3">
                    <a
                        href="/worlds/{worldId}/events"
                        class="inline-flex items-center rounded-md bg-purple-600 dark:bg-purple-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 dark:hover:bg-purple-400"
                    >
                        View Events
                    </a>
                    <button
                        on:click={handleExportWorld}
                        class="inline-flex items-center rounded-md bg-green-600 dark:bg-green-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 dark:hover:bg-green-400"
                        title="Export world as JSON"
                    >
                        Export
                    </button>
                    <button
                        on:click={handleImportClick}
                        disabled={importing}
                        class="inline-flex items-center rounded-md bg-blue-600 dark:bg-blue-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 dark:hover:bg-blue-400 disabled:opacity-50"
                        title="Import world from JSON"
                    >
                        {importing ? 'Importing...' : 'Import'}
                    </button>
                    <button
                        on:click={handleDuplicateWorld}
                        disabled={duplicating}
                        class="inline-flex items-center rounded-md bg-yellow-600 dark:bg-yellow-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-yellow-500 dark:hover:bg-yellow-400 disabled:opacity-50"
                        title="Duplicate this world"
                    >
                        {duplicating ? 'Duplicating...' : 'Duplicate'}
                    </button>
                    <a
                        href="/worlds/{worldId}/edit"
                        class="inline-flex items-center rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
                    >
                        Edit
                    </a>
                    <button
                        on:click={handleDeleteWorld}
                        class="inline-flex items-center rounded-md bg-red-600 dark:bg-red-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 dark:hover:bg-red-400"
                    >
                        Delete
                    </button>
                </div>
            </div>
        </div>

        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Stories</h2>
                <div class="flex items-center gap-3">
                    <a
                        href="/worlds/{worldId}/stories/archived"
                        class="rounded-md bg-gray-600 dark:bg-gray-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-gray-500 dark:hover:bg-gray-400"
                    >
                        View Archived
                    </a>
                    <a
                        href="/worlds/{worldId}/stories/new"
                        class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400"
                        >New Story</a
                    >
                </div>
            </div>

            {#if stories.length === 0}
                <div
                    class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700"
                >
                    <p class="text-sm text-gray-500 dark:text-gray-400">No stories yet.</p>
                </div>
            {:else}
                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
                    {#each stories as story}
                        <a
                            href="/stories/{story.id}"
                            class="block hover:bg-gray-50 dark:hover:bg-gray-800 transition duration-150 ease-in-out"
                        >
                            <div
                                class="relative flex items-center space-x-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-6 py-5 shadow-sm focus-within:ring-2 focus-within:ring-indigo-500 dark:focus-within:ring-indigo-400 focus-within:ring-offset-2 dark:focus-within:ring-offset-gray-900 hover:border-gray-400 dark:hover:border-gray-500"
                            >
                                <div class="min-w-0 flex-1">
                                    <div class="focus:outline-none">
                                        <span
                                            class="absolute inset-0"
                                            aria-hidden="true"
                                        ></span>
                                        <p
                                            class="text-sm font-medium text-gray-900 dark:text-gray-100"
                                        >
                                            {story.title}
                                        </p>
                                        <p
                                            class="truncate text-sm text-gray-500 dark:text-gray-400"
                                        >
                                            {story.synopsis || "No synopsis"}
                                        </p>
                                    </div>
                                </div>
                                <div
                                    class="flex-shrink-0 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400"
                                >
                                    <span
                                        class="inline-flex items-center rounded-full bg-green-50 dark:bg-green-900/30 px-2 py-1 text-xs font-medium text-green-700 dark:text-green-300 ring-1 ring-inset ring-green-600/20 dark:ring-green-500/30"
                                        >{story.status}</span
                                    >
                                </div>
                            </div>
                        </a>
                    {/each}
                </div>
            {/if}
        </div>

        <!-- Characters Section -->
        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Characters</h2>
                <div class="flex items-center gap-3">
                    <a
                        href="/worlds/{worldId}/characters"
                        class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
                    >
                        View All →
                    </a>
                    <a
                        href="/worlds/{worldId}/characters/new"
                        class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400"
                    >
                        + New Character
                    </a>
                </div>
            </div>

            {#if characters.length === 0}
                <div
                    class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-12 w-12 mx-auto text-gray-400 mb-3"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                        />
                    </svg>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">No characters yet.</p>
                    <a
                        href="/worlds/{worldId}/characters/new"
                        class="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                    >
                        Create First Character
                    </a>
                </div>
            {:else}
                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {#each characters as character}
                        <a
                            href="/worlds/{worldId}/characters/{character.id}"
                            class="block hover:bg-gray-50 dark:hover:bg-gray-800 transition duration-150 ease-in-out"
                        >
                            <div
                                class="relative flex flex-col rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-4 shadow-sm hover:border-gray-400 dark:hover:border-gray-500"
                            >
                                <div class="flex items-start justify-between mb-2">
                                    <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                                        {character.name}
                                    </p>
                                    <span
                                        class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {character.importance ===
                                        'major'
                                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                                            : character.importance === 'minor'
                                              ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                              : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'}"
                                    >
                                        {character.importance}
                                    </span>
                                </div>
                                {#if character.role}
                                    <p class="text-xs text-gray-500 dark:text-gray-400">
                                        {character.role}
                                    </p>
                                {/if}
                            </div>
                        </a>
                    {/each}
                </div>
                <div class="mt-4 text-center">
                    <a
                        href="/worlds/{worldId}/characters"
                        class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 font-medium"
                    >
                        View All Characters →
                    </a>
                </div>
            {/if}
        </div>

        <!-- Relationships Section -->
        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Character Relationships</h2>
                <div class="flex items-center gap-3">
                    <a
                        href="/worlds/{worldId}/relationships/graph"
                        class="text-sm text-purple-600 dark:text-purple-400 hover:text-purple-500"
                    >
                        View Graph →
                    </a>
                    <a
                        href="/worlds/{worldId}/relationships"
                        class="rounded-md bg-purple-600 dark:bg-purple-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 dark:hover:bg-purple-400"
                    >
                        Manage Relationships
                    </a>
                </div>
            </div>

            <div class="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-lg p-6 border border-purple-200 dark:border-purple-800">
                <div class="flex items-start gap-4">
                    <div class="flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                    </div>
                    <div class="flex-1">
                        <h3 class="text-sm font-semibold text-purple-900 dark:text-purple-200 mb-1">
                            Character Relationship Network
                        </h3>
                        <p class="text-sm text-purple-700 dark:text-purple-300 mb-3">
                            Define and visualize relationships between characters in your world. Track friendships, rivalries, alliances, and more.
                        </p>
                        <div class="flex items-center gap-3">
                            <a
                                href="/worlds/{worldId}/relationships"
                                class="text-sm font-medium text-purple-700 dark:text-purple-300 hover:text-purple-600 dark:hover:text-purple-200"
                            >
                                Browse Relationships →
                            </a>
                            <a
                                href="/worlds/{worldId}/relationships/graph"
                                class="text-sm font-medium text-purple-700 dark:text-purple-300 hover:text-purple-600 dark:hover:text-purple-200"
                            >
                                Explore Network Graph →
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Locations Section -->
        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Locations</h2>
                <div class="flex items-center gap-3">
                    <a
                        href="/worlds/{worldId}/locations"
                        class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
                    >
                        View All →
                    </a>
                    <a
                        href="/worlds/{worldId}/locations/new"
                        class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400"
                    >
                        + New Location
                    </a>
                </div>
            </div>

            {#if locations.length === 0}
                <div
                    class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-12 w-12 mx-auto text-gray-400 mb-3"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                        />
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                        />
                    </svg>
                    <p class="text-sm text-gray-500 dark:text-gray-400 mb-3">No locations yet.</p>
                    <a
                        href="/worlds/{worldId}/locations/new"
                        class="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                    >
                        Create First Location
                    </a>
                </div>
            {:else}
                <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {#each locations as location}
                        <a
                            href="/worlds/{worldId}/locations/{location.id}"
                            class="block hover:bg-gray-50 dark:hover:bg-gray-800 transition duration-150 ease-in-out"
                        >
                            <div
                                class="relative flex flex-col rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-5 py-4 shadow-sm hover:border-gray-400 dark:hover:border-gray-500"
                            >
                                <div class="flex items-start justify-between mb-2">
                                    <p class="text-sm font-medium text-gray-900 dark:text-gray-100">
                                        {location.name}
                                    </p>
                                    {#if location.location_type}
                                        <span
                                            class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                                        >
                                            {location.location_type}
                                        </span>
                                    {/if}
                                </div>
                                {#if location.parent_location_id}
                                    <p class="text-xs text-gray-500 dark:text-gray-400">
                                        Child location
                                    </p>
                                {/if}
                            </div>
                        </a>
                    {/each}
                </div>
                <div class="mt-4 text-center">
                    <a
                        href="/worlds/{worldId}/locations"
                        class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 font-medium"
                    >
                        View All Locations →
                    </a>
                </div>
            {/if}
        </div>
    </div>
{/if}
