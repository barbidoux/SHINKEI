<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import type { EventType, WorldEvent } from "$lib/types";

    let t = 0;
    let label_time = "";
    let location = "";
    let type: EventType = "major";
    let summary = "";
    let description = "";
    let loading = false;
    let loadingEvent = true;
    let error = "";

    $: worldId = $page.params.id;
    $: eventId = $page.params.event_id;

    const eventTypes: { value: EventType; label: string; description: string }[] = [
        {
            value: "major",
            label: "Major Event",
            description: "Significant event that impacts multiple stories",
        },
        {
            value: "minor",
            label: "Minor Event",
            description: "Smaller event with localized impact",
        },
        {
            value: "backstory",
            label: "Backstory",
            description: "Historical event in the world's past",
        },
        {
            value: "milestone",
            label: "Milestone",
            description: "Key turning point or achievement",
        },
    ];

    onMount(async () => {
        try {
            const event = await api.get<WorldEvent>(
                `/worlds/${worldId}/events/${eventId}`,
            );
            t = event.t;
            label_time = event.label_time || "";
            location = event.location || "";
            type = event.type;
            summary = event.summary;
            description = event.description || "";
            loadingEvent = false;
        } catch (e: any) {
            error = e.message || "Failed to load event";
            loadingEvent = false;
        }
    });

    async function handleSubmit() {
        loading = true;
        error = "";

        try {
            const eventData = {
                t,
                label_time: label_time || undefined,
                location: location || undefined,
                type,
                summary,
                description: description || undefined,
            };

            await api.put(`/worlds/${worldId}/events/${eventId}`, eventData);
            goto(`/worlds/${worldId}/events`);
        } catch (e: any) {
            error = e.message || "Failed to update event";
        } finally {
            loading = false;
        }
    }
</script>

{#if loadingEvent}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-gray-500">Loading event...</p>
        </div>
    </div>
{:else if error && !summary}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-red-500">{error}</p>
            <button
                on:click={() => goto(`/worlds/${worldId}/events`)}
                class="mt-4 text-indigo-600 hover:text-indigo-500"
            >
                ← Back to Events
            </button>
        </div>
    </div>
{:else}
    <div class="max-w-3xl mx-auto py-8">
        <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900">Edit World Event</h1>
            <p class="mt-2 text-sm text-gray-500">
                Update this canonical event in your world's timeline
            </p>
        </div>

        <form on:submit|preventDefault={handleSubmit} class="space-y-6">
            <!-- Timeline Position (t) -->
            <div>
                <label
                    for="t"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Timeline Position (t) <span class="text-red-500">*</span>
                </label>
                <input
                    type="number"
                    id="t"
                    bind:value={t}
                    required
                    step="0.01"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="0"
                />
                <p class="mt-1 text-xs text-gray-500">
                    Objective world time value (can be negative or decimal)
                </p>
            </div>

            <!-- Label Time -->
            <div>
                <label
                    for="label_time"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Time Label (optional)
                </label>
                <input
                    type="text"
                    id="label_time"
                    bind:value={label_time}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder='e.g., "Year 2145" or "The Great War"'
                />
                <p class="mt-1 text-xs text-gray-500">
                    Human-readable timestamp for this event
                </p>
            </div>

            <!-- Event Type -->
            <div>
                <label
                    for="type"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Event Type
                </label>
                <select
                    id="type"
                    bind:value={type}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                    {#each eventTypes as eventType}
                        <option value={eventType.value}
                            >{eventType.label}</option
                        >
                    {/each}
                </select>
                {#each eventTypes as eventType}
                    {#if type === eventType.value}
                        <p class="mt-1 text-sm text-gray-500">
                            {eventType.description}
                        </p>
                    {/if}
                {/each}
            </div>

            <!-- Summary -->
            <div>
                <label
                    for="summary"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Summary <span class="text-red-500">*</span>
                </label>
                <input
                    type="text"
                    id="summary"
                    bind:value={summary}
                    required
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Brief description of what happens"
                />
            </div>

            <!-- Location -->
            <div>
                <label
                    for="location"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Location (optional)
                </label>
                <input
                    type="text"
                    id="location"
                    bind:value={location}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Where this event takes place"
                />
            </div>

            <!-- Description -->
            <div>
                <label
                    for="description"
                    class="block text-sm font-medium text-gray-700 mb-2"
                >
                    Full Description (optional)
                </label>
                <textarea
                    id="description"
                    bind:value={description}
                    rows="6"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="Detailed description of the event and its significance..."
                ></textarea>
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
                    on:click={() => goto(`/worlds/${worldId}/events`)}
                    class="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={loading || !summary.trim()}
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
