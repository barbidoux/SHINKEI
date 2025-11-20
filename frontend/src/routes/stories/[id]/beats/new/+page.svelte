<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import type { BeatType, WorldEvent } from "$lib/types";

    let content = "";
    let type: BeatType = "scene";
    let summary = "";
    let local_time_label = "";
    let world_event_id = "";
    let loading = false;
    let error = "";

    let worldEvents: WorldEvent[] = [];
    let loadingEvents = true;
    let worldId = "";

    $: storyId = $page.params.id;

    const beatTypes: { value: BeatType; label: string }[] = [
        { value: "scene", label: "Scene" },
        { value: "log", label: "Log Entry" },
        { value: "memory", label: "Memory" },
        { value: "dialogue", label: "Dialogue" },
        { value: "description", label: "Description" },
    ];

    onMount(async () => {
        try {
            // Fetch story to get world_id
            const story = await api.get<{ world_id: string }>(
                `/stories/${storyId}`,
            );
            worldId = story.world_id;

            // Fetch world events for this world
            const events = await api.get<WorldEvent[]>(
                `/worlds/${worldId}/events`,
            );
            worldEvents = events;
        } catch (e: any) {
            console.error("Failed to load world events:", e);
        } finally {
            loadingEvents = false;
        }
    });

    async function handleSubmit() {
        loading = true;
        error = "";

        try {
            const beatData = {
                content,
                type,
                summary: summary || undefined,
                local_time_label: local_time_label || undefined,
                world_event_id: world_event_id || undefined,
                generated_by: "user" as const,
            };

            await api.post(`/stories/${storyId}/beats`, beatData);
            goto(`/stories/${storyId}`);
        } catch (e: any) {
            error = e.message || "Failed to create beat";
        } finally {
            loading = false;
        }
    }
</script>

<div class="max-w-3xl mx-auto py-8">
    <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Create New Beat</h1>
        <p class="mt-2 text-sm text-gray-500">
            Manually write a new story beat
        </p>
    </div>

    <form on:submit|preventDefault={handleSubmit} class="space-y-6">
        <!-- Beat Type -->
        <div>
            <label
                for="type"
                class="block text-sm font-medium text-gray-700 mb-2"
            >
                Beat Type
            </label>
            <select
                id="type"
                bind:value={type}
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
            >
                {#each beatTypes as beatType}
                    <option value={beatType.value}>{beatType.label}</option>
                {/each}
            </select>
        </div>

        <!-- Content -->
        <div>
            <label
                for="content"
                class="block text-sm font-medium text-gray-700 mb-2"
            >
                Content <span class="text-red-500">*</span>
            </label>
            <textarea
                id="content"
                bind:value={content}
                required
                rows="12"
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="Write your story beat content here..."
            ></textarea>
        </div>

        <!-- Summary -->
        <div>
            <label
                for="summary"
                class="block text-sm font-medium text-gray-700 mb-2"
            >
                Summary (optional)
            </label>
            <input
                type="text"
                id="summary"
                bind:value={summary}
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="Brief summary of this beat"
            />
        </div>

        <!-- Local Time Label -->
        <div>
            <label
                for="local_time_label"
                class="block text-sm font-medium text-gray-700 mb-2"
            >
                Time Label (optional)
            </label>
            <input
                type="text"
                id="local_time_label"
                bind:value={local_time_label}
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder='e.g., "Day 1, Morning" or "Log 0017"'
            />
            <p class="mt-1 text-xs text-gray-500">
                In-world timestamp or narrative label
            </p>
        </div>

        <!-- World Event Link -->
        <div>
            <label
                for="world_event"
                class="block text-sm font-medium text-gray-700 mb-2"
            >
                Link to World Event (optional)
            </label>
            {#if loadingEvents}
                <div class="text-sm text-gray-500">Loading events...</div>
            {:else}
                <select
                    id="world_event"
                    bind:value={world_event_id}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                    <option value="">None - No event link</option>
                    {#each worldEvents as event}
                        <option value={event.id}>
                            {event.label_time || `t=${event.t}`} - {event.summary}
                        </option>
                    {/each}
                </select>
                <p class="mt-1 text-xs text-gray-500">
                    Connect this beat to a canonical world event for story
                    intersection
                </p>
            {/if}
        </div>

        <!-- Error Display -->
        {#if error}
            <div
                class="rounded-md bg-red-50 p-4 border border-red-200"
            >
                <p class="text-sm text-red-800">{error}</p>
            </div>
        {/if}

        <!-- Actions -->
        <div class="flex items-center justify-between pt-4">
            <button
                type="button"
                on:click={() => goto(`/stories/${storyId}`)}
                class="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
            >
                Cancel
            </button>
            <button
                type="submit"
                disabled={loading || !content.trim()}
                class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {#if loading}
                    Creating...
                {:else}
                    Create Beat
                {/if}
            </button>
        </div>
    </form>
</div>
