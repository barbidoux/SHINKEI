<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import { BeatModificationPanel, CoherenceChecker } from "$lib/components";
    import AIThoughtsPanel from "$lib/components/AIThoughtsPanel.svelte";
    import type { BeatType, StoryBeat, WorldEvent, BeatResponse } from "$lib/types";

    let beat: StoryBeat | null = null;
    let content = "";
    let type: BeatType = "scene";
    let summary = "";
    let local_time_label = "";
    let world_event_id = "";
    let loading = false;
    let loadingBeat = true;
    let error = "";
    let showModificationPanel = false;

    let worldEvents: WorldEvent[] = [];
    let loadingEvents = true;
    let worldId = "";

    $: storyId = $page.params.id;
    $: beatId = $page.params.beat_id;

    const beatTypes: { value: BeatType; label: string }[] = [
        { value: "scene", label: "Scene" },
        { value: "log", label: "Log Entry" },
        { value: "memory", label: "Memory" },
        { value: "dialogue", label: "Dialogue" },
        { value: "description", label: "Description" },
    ];

    onMount(async () => {
        try {
            // Fetch the beat data
            const beatData = await api.get<StoryBeat>(
                `/stories/${storyId}/beats/${beatId}`,
            );
            beat = beatData;
            content = beatData.content;
            type = beatData.type;
            summary = beatData.summary || "";
            local_time_label = beatData.local_time_label || "";
            world_event_id = beatData.world_event_id || "";

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

            loadingEvents = false;
            loadingBeat = false;
        } catch (e: any) {
            error = e.message || "Failed to load beat";
            loadingBeat = false;
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
            };

            await api.put(`/stories/${storyId}/beats/${beatId}`, beatData);
            goto(`/stories/${storyId}`);
        } catch (e: any) {
            error = e.message || "Failed to update beat";
        } finally {
            loading = false;
        }
    }

    function handleModificationApplied() {
        showModificationPanel = false;
        // Reload the beat data
        window.location.reload();
    }
</script>

{#if loadingBeat}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-gray-500">Loading beat...</p>
        </div>
    </div>
{:else if error && !content}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-red-500">{error}</p>
            <button
                on:click={() => goto(`/stories/${storyId}`)}
                class="mt-4 text-indigo-600 hover:text-indigo-500"
            >
                ← Back to Story
            </button>
        </div>
    </div>
{:else}
    <div class="max-w-3xl mx-auto py-8">
        <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Edit Beat</h1>
            <p class="mt-2 text-sm text-gray-500">
                Update your story beat content and metadata
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
                        <option value={beatType.value}
                            >{beatType.label}</option
                        >
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
                <div class="rounded-md bg-red-50 p-4 border border-red-200">
                    <p class="text-sm text-red-800">{error}</p>
                </div>
            {/if}

            <!-- Actions -->
            <div class="flex items-center justify-between pt-4">
                <div class="flex items-center gap-3">
                    <button
                        type="button"
                        on:click={() => goto(`/stories/${storyId}`)}
                        class="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                    >
                        Cancel
                    </button>
                    <button
                        type="button"
                        on:click={() => showModificationPanel = true}
                        class="rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600"
                    >
                        🤖 Modify with AI
                    </button>
                </div>
                <button
                    type="submit"
                    disabled={loading || !content.trim()}
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

        <!-- AI Thoughts Panel -->
        {#if beat && (beat.generated_by === "ai" || beat.generation_reasoning)}
            <div class="mt-6">
                <AIThoughtsPanel
                    beat={beat as BeatResponse}
                    onUpdate={async () => {
                        // Refresh beat data after reasoning update
                        const updatedBeat = await api.get<StoryBeat>(
                            `/stories/${storyId}/beats/${beatId}`,
                        );
                        beat = updatedBeat;
                    }}
                />
            </div>
        {/if}

        <!-- Coherence Checker -->
        {#if beat}
            <div class="mt-6">
                <CoherenceChecker storyId={storyId} beatId={beatId} />
            </div>
        {/if}
    </div>
{/if}

<!-- Modification Panel (Slide-in from Right) -->
{#if showModificationPanel && beat}
    <!-- Backdrop -->
    <div
        class="fixed inset-0 bg-black/50 z-40 transition-opacity"
        on:click={() => showModificationPanel = false}
        on:keydown={(e) => e.key === "Escape" && (showModificationPanel = false)}
        role="button"
        tabindex="0"
    ></div>

    <!-- Panel -->
    <div class="fixed right-0 top-0 bottom-0 w-full md:w-2/3 lg:w-1/2 max-w-4xl z-50 transform transition-transform duration-300">
        <BeatModificationPanel
            beat={beat as BeatResponse}
            storyId={storyId ?? ""}
            onModificationApplied={handleModificationApplied}
            onClose={() => showModificationPanel = false}
        />
    </div>
{/if}
