<script lang="ts">
    import { page } from "$app/stores";
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { api } from "$lib/api";
    import { WorldEventTimeline, StoryIntersectionView, EventDependencyGraph } from "$lib/components";
    import type { WorldEvent, World } from "$lib/types";

    let world: World | null = null;
    let events: WorldEvent[] = [];
    let loading = true;
    let error = "";
    let viewMode: "list" | "timeline" | "graph" = "list";
    let showIntersection = false;
    let selectedEvent: WorldEvent | null = null;

    $: worldId = $page.params.id;

    // Load view preference from localStorage
    onMount(() => {
        const savedView = localStorage.getItem("worldEventsViewMode");
        if (savedView === "timeline" || savedView === "list" || savedView === "graph") {
            viewMode = savedView as "list" | "timeline" | "graph";
        }
    });

    // Save view preference
    $: if (viewMode) {
        localStorage.setItem("worldEventsViewMode", viewMode);
    }

    onMount(async () => {
        try {
            const [worldData, eventsData] = await Promise.all([
                api.get<World>(`/worlds/${worldId}`),
                api.get<WorldEvent[]>(`/worlds/${worldId}/events`),
            ]);
            world = worldData;
            events = eventsData.sort((a, b) => a.t - b.t); // Sort by timeline
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    });

    async function handleDeleteEvent(eventId: string) {
        if (
            !confirm(
                "Are you sure you want to delete this event? This will affect all story beats linked to it. This action cannot be undone.",
            )
        ) {
            return;
        }

        try {
            await api.delete(`/worlds/${worldId}/events/${eventId}`);
            // Reload the page to refresh the events list
            window.location.reload();
        } catch (e: any) {
            alert(`Failed to delete event: ${e.message}`);
        }
    }

    function getEventTypeLabel(type: string): string {
        const labels: Record<string, string> = {
            major: "Major Event",
            minor: "Minor Event",
            backstory: "Backstory",
            milestone: "Milestone",
        };
        return labels[type] || type;
    }

    function handleEventClick(event: WorldEvent) {
        selectedEvent = event;
        showIntersection = true;
    }

    function handleCloseIntersection() {
        showIntersection = false;
        selectedEvent = null;
    }

    function handleViewIntersection(event: WorldEvent) {
        selectedEvent = event;
        showIntersection = true;
    }
</script>

{#if loading}
    <div class="text-center py-12">Loading events...</div>
{:else if error}
    <div class="text-center py-12 text-red-500">{error}</div>
{:else if world}
    <div class="space-y-8">
        <div class="border-b border-gray-200 pb-5">
            <div class="flex items-center justify-between">
                <div>
                    <h1 class="text-3xl font-bold leading-6 text-gray-900">
                        World Events Timeline
                    </h1>
                    <p class="mt-2 max-w-4xl text-sm text-gray-500">
                        Canonical events in <span class="font-medium"
                            >{world.name}</span
                        >
                    </p>
                </div>
                <a
                    href="/worlds/{worldId}/events/new"
                    class="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                >
                    + Create Event
                </a>
            </div>
            <div class="mt-4 flex items-center justify-between">
                <a
                    href="/worlds/{worldId}"
                    class="text-sm font-medium text-indigo-600 hover:text-indigo-500"
                    >← Back to World</a
                >

                <!-- View Mode Toggle -->
                <div class="inline-flex rounded-md shadow-sm" role="group">
                    <button
                        type="button"
                        on:click={() => (viewMode = "list")}
                        class="px-4 py-2 text-sm font-medium rounded-l-lg border border-gray-300 {viewMode === 'list' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}"
                    >
                        List View
                    </button>
                    <button
                        type="button"
                        on:click={() => (viewMode = "timeline")}
                        class="px-4 py-2 text-sm font-medium border border-gray-300 border-l-0 {viewMode === 'timeline' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}"
                    >
                        Timeline View
                    </button>
                    <button
                        type="button"
                        on:click={() => (viewMode = "graph")}
                        class="px-4 py-2 text-sm font-medium rounded-r-lg border border-gray-300 border-l-0 {viewMode === 'graph' ? 'bg-indigo-600 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'}"
                    >
                        Dependency Graph
                    </button>
                </div>
            </div>
        </div>

        <!-- Timeline View -->
        {#if viewMode === "timeline"}
            <WorldEventTimeline {events} onEventClick={handleEventClick} />
        {:else if viewMode === "graph"}
            <!-- Dependency Graph View -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <EventDependencyGraph {worldId} apiUrl={import.meta.env.VITE_API_URL} />
            </div>
        {:else}
            <!-- List View -->
            <div class="space-y-4">
                {#if events.length === 0}
                    <div
                        class="text-center py-12 bg-white rounded-lg shadow border border-gray-200"
                    >
                        <p class="text-sm text-gray-500">
                            No events yet. Create your first canonical world event!
                        </p>
                    </div>
                {:else}
                    {#each events as event}
                        <div
                            class="relative rounded-lg border border-gray-300 bg-white px-6 py-5 shadow-sm hover:border-gray-400"
                        >
                            <div class="flex items-start justify-between">
                                <div class="flex-1">
                                    <div class="flex items-center gap-3 mb-2">
                                        <span
                                            class="inline-flex items-center rounded-md bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 ring-1 ring-inset ring-indigo-600/20"
                                        >
                                            t = {event.t}
                                        </span>
                                        {#if event.label_time}
                                            <span
                                                class="inline-flex items-center rounded-md bg-gray-50 px-2.5 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10"
                                            >
                                                {event.label_time}
                                            </span>
                                        {/if}
                                        <span
                                            class="inline-flex items-center rounded-md bg-purple-50 px-2 py-1 text-xs font-medium text-purple-700 ring-1 ring-inset ring-purple-600/20"
                                        >
                                            {getEventTypeLabel(event.type)}
                                        </span>
                                    </div>

                                    <h3 class="text-sm font-semibold text-gray-900">
                                        {event.summary}
                                    </h3>

                                    {#if event.location}
                                        <p class="mt-1 text-xs text-gray-500">
                                            Location: {event.location}
                                        </p>
                                    {/if}

                                    {#if event.description}
                                        <p
                                            class="mt-2 text-sm text-gray-600 whitespace-pre-wrap"
                                        >
                                            {event.description}
                                        </p>
                                    {/if}
                                </div>

                                <div class="flex items-center gap-3 ml-4">
                                    <button
                                        on:click={() => handleViewIntersection(event)}
                                        class="text-sm text-purple-600 hover:text-purple-500 font-medium"
                                    >
                                        View Intersection
                                    </button>
                                    <a
                                        href="/worlds/{worldId}/events/{event.id}/edit"
                                        class="text-sm text-indigo-600 hover:text-indigo-500"
                                    >
                                        Edit
                                    </a>
                                    <button
                                        on:click={() => handleDeleteEvent(event.id)}
                                        class="text-sm text-red-600 hover:text-red-500"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        </div>
                    {/each}
                {/if}
            </div>
        {/if}
    </div>
{/if}

<!-- Story Intersection Modal -->
{#if showIntersection && selectedEvent}
    <!-- Backdrop -->
    <div
        class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40"
        on:click={handleCloseIntersection}
        on:keydown={(e) => e.key === "Escape" && handleCloseIntersection()}
        role="button"
        tabindex="0"
    ></div>

    <!-- Modal Panel -->
    <div
        class="fixed inset-y-0 right-0 w-full max-w-4xl bg-white shadow-xl z-50 overflow-y-auto"
    >
        <div class="p-6">
            <StoryIntersectionView
                eventId={selectedEvent.id}
                eventSummary={selectedEvent.summary}
                onClose={handleCloseIntersection}
            />
        </div>
    </div>
{/if}
