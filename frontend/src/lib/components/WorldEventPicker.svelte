<script lang="ts">
    import { api } from "$lib/api";
    import { onMount } from "svelte";

    export let worldId: string;
    export let selectedEventId: string = "";
    export let onSelect: (eventId: string) => void = () => {};

    interface WorldEvent {
        id: string;
        t: number;
        label_time: string;
        location_id: string | null;
        type: string;
        summary: string;
        tags: string[];
        created_at: string;
        updated_at: string;
    }

    let events: WorldEvent[] = [];
    let loading: boolean = false;
    let error: string = "";
    let searchQuery: string = "";
    let selectedType: string = "all";
    let showPicker: boolean = false;

    $: filteredEvents = events.filter((event) => {
        const matchesSearch = searchQuery === "" ||
            event.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
            event.label_time.toLowerCase().includes(searchQuery.toLowerCase()) ||
            event.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
            event.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));

        const matchesType = selectedType === "all" || event.type === selectedType;

        return matchesSearch && matchesType;
    });

    $: eventTypes = ["all", ...new Set(events.map(e => e.type))];

    $: selectedEvent = events.find(e => e.id === selectedEventId);

    onMount(async () => {
        await loadEvents();
    });

    async function loadEvents() {
        loading = true;
        error = "";
        try {
            const response = await api.get<{ events: WorldEvent[]; total: number }>(
                `/worlds/${worldId}/events?limit=1000`
            );
            events = response.events.sort((a, b) => a.t - b.t);
        } catch (e: any) {
            error = e.message || "Failed to load world events";
            console.error("Failed to load world events:", e);
        } finally {
            loading = false;
        }
    }

    function selectEvent(eventId: string) {
        selectedEventId = eventId;
        onSelect(eventId);
        showPicker = false;
    }

    function clearSelection() {
        selectedEventId = "";
        onSelect("");
    }
</script>

<div class="world-event-picker">
    <!-- Selected Event Display (Compact) -->
    {#if selectedEvent}
        <div class="mb-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-md border border-green-200 dark:border-green-700">
            <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="inline-flex items-center rounded-full bg-green-100 dark:bg-green-900/50 px-2 py-0.5 text-xs font-medium text-green-800 dark:text-green-200">
                            {selectedEvent.type}
                        </span>
                        <span class="text-xs text-gray-600 dark:text-gray-400">
                            {selectedEvent.label_time}
                        </span>
                    </div>
                    <p class="text-sm text-gray-900 dark:text-gray-100 truncate">
                        {selectedEvent.summary}
                    </p>
                </div>
                <button
                    type="button"
                    on:click={clearSelection}
                    class="ml-2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                    title="Clear selection"
                >
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>
        </div>
    {/if}

    <!-- Picker Toggle Button -->
    <button
        type="button"
        on:click={() => showPicker = !showPicker}
        class="w-full px-3 py-2 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center justify-between"
    >
        <span>
            {selectedEvent ? "Change World Event" : "Select World Event"}
        </span>
        <svg class="w-4 h-4 transition-transform {showPicker ? 'rotate-180' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
    </button>

    <!-- Event Picker Panel -->
    {#if showPicker}
        <div class="mt-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 shadow-lg max-h-96 overflow-hidden flex flex-col">
            <!-- Search and Filter Controls -->
            <div class="p-3 border-b border-gray-200 dark:border-gray-700 space-y-2">
                <input
                    type="text"
                    bind:value={searchQuery}
                    placeholder="Search events..."
                    class="w-full px-3 py-2 text-sm rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                />
                <select
                    bind:value={selectedType}
                    class="w-full px-3 py-2 text-sm rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                >
                    {#each eventTypes as type}
                        <option value={type}>
                            {type === "all" ? "All Types" : type}
                        </option>
                    {/each}
                </select>
            </div>

            <!-- Event List -->
            <div class="flex-1 overflow-y-auto">
                {#if loading}
                    <div class="p-4 text-center text-gray-500 dark:text-gray-400">
                        <svg class="animate-spin h-5 w-5 mx-auto mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Loading events...
                    </div>
                {:else if error}
                    <div class="p-4 text-center text-red-600 dark:text-red-400">
                        {error}
                    </div>
                {:else if filteredEvents.length === 0}
                    <div class="p-4 text-center text-gray-500 dark:text-gray-400">
                        {searchQuery || selectedType !== "all" ? "No events match your filters" : "No world events found"}
                    </div>
                {:else}
                    <div class="divide-y divide-gray-200 dark:divide-gray-700">
                        {#each filteredEvents as event}
                            <button
                                type="button"
                                on:click={() => selectEvent(event.id)}
                                class="w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors {event.id === selectedEventId ? 'bg-blue-50 dark:bg-blue-900/20' : ''}"
                            >
                                <div class="flex items-start justify-between gap-2">
                                    <div class="flex-1 min-w-0">
                                        <div class="flex items-center gap-2 mb-1">
                                            <span class="inline-flex items-center rounded-full bg-purple-100 dark:bg-purple-900/50 px-2 py-0.5 text-xs font-medium text-purple-800 dark:text-purple-200">
                                                {event.type}
                                            </span>
                                            <span class="text-xs text-gray-600 dark:text-gray-400">
                                                {event.label_time}
                                            </span>
                                            <span class="text-xs text-gray-500 dark:text-gray-500">
                                                t={event.t}
                                            </span>
                                        </div>
                                        <p class="text-sm text-gray-900 dark:text-gray-100 mb-1">
                                            {event.summary}
                                        </p>
                                        {#if event.tags.length > 0}
                                            <div class="flex flex-wrap gap-1">
                                                {#each event.tags as tag}
                                                    <span class="inline-flex items-center rounded bg-gray-100 dark:bg-gray-700 px-1.5 py-0.5 text-xs text-gray-600 dark:text-gray-400">
                                                        {tag}
                                                    </span>
                                                {/each}
                                            </div>
                                        {/if}
                                    </div>
                                    {#if event.id === selectedEventId}
                                        <svg class="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                                        </svg>
                                    {/if}
                                </div>
                            </button>
                        {/each}
                    </div>
                {/if}
            </div>

            <!-- Footer -->
            <div class="p-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 text-xs text-gray-600 dark:text-gray-400 text-center">
                {filteredEvents.length} of {events.length} events
            </div>
        </div>
    {/if}
</div>

<style>
    .world-event-picker {
        position: relative;
    }
</style>
