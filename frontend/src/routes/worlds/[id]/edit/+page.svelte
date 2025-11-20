<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import type { World, ChronologyMode, WorldLaws } from "$lib/types";

    let name = "";
    let description = "";
    let tone = "";
    let backdrop = "";
    let chronology_mode: ChronologyMode = "linear";
    let physics = "";
    let metaphysics = "";
    let social = "";
    let forbidden = "";
    let loading = false;
    let loadingWorld = true;
    let error = "";

    $: worldId = $page.params.id;

    const chronologyModes: {
        value: ChronologyMode;
        label: string;
        description: string;
    }[] = [
        {
            value: "linear",
            label: "Linear",
            description: "Events follow a strict chronological order",
        },
        {
            value: "fragmented",
            label: "Fragmented",
            description: "Non-linear narrative with flashbacks and time jumps",
        },
        {
            value: "timeless",
            label: "Timeless",
            description: "No fixed timeline, events float in time",
        },
    ];

    onMount(async () => {
        try {
            const world = await api.get<World>(`/worlds/${worldId}`);
            name = world.name;
            description = world.description || "";
            tone = world.tone || "";
            backdrop = world.backdrop || "";
            chronology_mode = world.chronology_mode;
            physics = world.laws.physics || "";
            metaphysics = world.laws.metaphysics || "";
            social = world.laws.social || "";
            forbidden = world.laws.forbidden || "";
            loadingWorld = false;
        } catch (e: any) {
            error = e.message || "Failed to load world";
            loadingWorld = false;
        }
    });

    async function handleSubmit() {
        loading = true;
        error = "";

        try {
            const laws: WorldLaws = {};
            if (physics) laws.physics = physics;
            if (metaphysics) laws.metaphysics = metaphysics;
            if (social) laws.social = social;
            if (forbidden) laws.forbidden = forbidden;

            const worldData = {
                name,
                description: description || undefined,
                tone: tone || undefined,
                backdrop: backdrop || undefined,
                laws,
                chronology_mode,
            };

            await api.put(`/worlds/${worldId}`, worldData);
            goto(`/worlds/${worldId}`);
        } catch (e: any) {
            error = e.message || "Failed to update world";
        } finally {
            loading = false;
        }
    }
</script>

{#if loadingWorld}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-gray-500">Loading world...</p>
        </div>
    </div>
{:else if error && !name}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-red-500">{error}</p>
            <button
                on:click={() => goto("/worlds")}
                class="mt-4 text-indigo-600 hover:text-indigo-500"
            >
                ← Back to Worlds
            </button>
        </div>
    </div>
{:else}
    <div class="max-w-3xl mx-auto py-8">
        <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Edit World</h1>
            <p class="mt-2 text-sm text-gray-500">
                Update your narrative world settings
            </p>
        </div>

        <form on:submit|preventDefault={handleSubmit} class="space-y-6">
            <!-- Name -->
            <div>
                <label
                    for="name"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    World Name <span class="text-red-500">*</span>
                </label>
                <input
                    type="text"
                    id="name"
                    bind:value={name}
                    required
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="My Narrative World"
                />
            </div>

            <!-- Description -->
            <div>
                <label
                    for="description"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Overview (optional)
                </label>
                <textarea
                    id="description"
                    bind:value={description}
                    rows="3"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="A brief overview of this world..."
                ></textarea>
            </div>

            <!-- Tone -->
            <div>
                <label
                    for="tone"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Tone (optional)
                </label>
                <input
                    type="text"
                    id="tone"
                    bind:value={tone}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., dark, whimsical, gritty, hopeful"
                />
                <p class="mt-1 text-xs text-gray-500">
                    The emotional atmosphere and feel of this world
                </p>
            </div>

            <!-- Backdrop -->
            <div>
                <label
                    for="backdrop"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Backdrop (optional)
                </label>
                <textarea
                    id="backdrop"
                    bind:value={backdrop}
                    rows="3"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="The historical, cultural, or environmental context..."
                ></textarea>
                <p class="mt-1 text-xs text-gray-500">
                    The setting and context in which stories unfold
                </p>
            </div>

            <!-- Chronology Mode -->
            <div>
                <label
                    for="chronology_mode"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Chronology Mode
                </label>
                <select
                    id="chronology_mode"
                    bind:value={chronology_mode}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                    {#each chronologyModes as mode}
                        <option value={mode.value}>{mode.label}</option>
                    {/each}
                </select>
                {#each chronologyModes as mode}
                    {#if chronology_mode === mode.value}
                        <p class="mt-1 text-sm text-gray-500">
                            {mode.description}
                        </p>
                    {/if}
                {/each}
            </div>

            <!-- World Laws Section -->
            <div class="border-t border-gray-200 pt-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">
                    World Laws (Optional)
                </h3>
                <p class="text-sm text-gray-500 mb-4">
                    Define the rules and constraints that govern this world
                </p>

                <div class="space-y-4">
                    <!-- Physics -->
                    <div>
                        <label
                            for="physics"
                            class="block text-sm font-medium text-gray-700 mb-2"
                        >
                            Physical Laws
                        </label>
                        <textarea
                            id="physics"
                            bind:value={physics}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="How does the physical world work? Gravity, magic, technology..."
                        ></textarea>
                    </div>

                    <!-- Metaphysics -->
                    <div>
                        <label
                            for="metaphysics"
                            class="block text-sm font-medium text-gray-700 mb-2"
                        >
                            Metaphysical Laws
                        </label>
                        <textarea
                            id="metaphysics"
                            bind:value={metaphysics}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="Souls, afterlife, consciousness, reality..."
                        ></textarea>
                    </div>

                    <!-- Social -->
                    <div>
                        <label
                            for="social"
                            class="block text-sm font-medium text-gray-700 mb-2"
                        >
                            Social Laws
                        </label>
                        <textarea
                            id="social"
                            bind:value={social}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="Cultural norms, taboos, hierarchies, customs..."
                        ></textarea>
                    </div>

                    <!-- Forbidden -->
                    <div>
                        <label
                            for="forbidden"
                            class="block text-sm font-medium text-gray-700 mb-2"
                        >
                            Forbidden Elements
                        </label>
                        <textarea
                            id="forbidden"
                            bind:value={forbidden}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="What should never appear in this world?"
                        ></textarea>
                    </div>
                </div>
            </div>

            <!-- Error Display -->
            {#if error}
                <div class="rounded-md bg-red-50 p-4 border border-red-200">
                    <p class="text-sm text-red-800">{error}</p>
                </div>
            {/if}

            <!-- Actions -->
            <div class="flex items-center justify-between pt-4">
                <button
                    type="button"
                    on:click={() => goto(`/worlds/${worldId}`)}
                    class="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={loading || !name.trim()}
                    class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {#if loading}
                        Saving...
                    {:else}
                        Save Changes
                    {/if}
                </button>
            </div>
        </form>
    </div>
{/if}
