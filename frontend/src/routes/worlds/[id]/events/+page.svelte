<script lang="ts">
    import { page } from "$app/stores";
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";
    import { api } from "$lib/api";
    import { WorldEventTimeline, StoryIntersectionView, EventDependencyGraph, AIGenerationOptions } from "$lib/components";
    import type { WorldEvent, World, Character, Location } from "$lib/types";
    import type { EventSuggestion, EventSuggestionsResponse, AIProvider } from "$lib/types/entity-generation";

    let world: World | null = null;
    let events: WorldEvent[] = [];
    let characters: Character[] = [];
    let locations: Location[] = [];
    let loading = true;
    let error = "";
    let viewMode: "list" | "timeline" | "graph" = "list";
    let showIntersection = false;
    let selectedEvent: WorldEvent | null = null;

    // AI Generation state
    let showAIInputModal = false;
    let showAIResultsModal = false;
    let aiGenerating = false;
    let aiError = "";
    let aiSuggestions: EventSuggestion[] = [];

    // AI Generation parameters
    let aiEventType = "";
    let aiTimeRangeMin: number | null = null;
    let aiTimeRangeMax: number | null = null;
    let aiLocationId = "";
    let aiInvolvingCharacterIds: string[] = [];
    let aiCausedByEventIds: string[] = [];
    let aiUserPrompt = "";
    let aiProvider: AIProvider | null = null;
    let aiModel = "";
    let aiTemperature: number | null = null;
    let aiOptionsExpanded = false;

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
            const [worldData, eventsData, charactersData, locationsData] = await Promise.all([
                api.get<World>(`/worlds/${worldId}`),
                api.get<WorldEvent[]>(`/worlds/${worldId}/events`),
                api.get<Character[]>(`/worlds/${worldId}/characters`),
                api.get<Location[]>(`/worlds/${worldId}/locations`),
            ]);
            world = worldData;
            events = eventsData.sort((a, b) => a.t - b.t); // Sort by timeline
            characters = charactersData;
            locations = locationsData;
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

    // AI Generation Functions
    function openAIGenerationModal() {
        // Reset form
        aiEventType = "";
        aiTimeRangeMin = null;
        aiTimeRangeMax = null;
        aiLocationId = "";
        aiInvolvingCharacterIds = [];
        aiCausedByEventIds = [];
        aiUserPrompt = "";
        aiProvider = null;
        aiModel = "";
        aiTemperature = null;
        aiOptionsExpanded = false;
        aiError = "";
        showAIInputModal = true;
    }

    async function generateWithAI() {
        aiGenerating = true;
        aiError = "";

        try {
            const requestBody: Record<string, any> = {};
            if (aiEventType) requestBody.event_type = aiEventType;
            if (aiTimeRangeMin !== null) requestBody.time_range_min = aiTimeRangeMin;
            if (aiTimeRangeMax !== null) requestBody.time_range_max = aiTimeRangeMax;
            if (aiLocationId) requestBody.location_id = aiLocationId;
            if (aiInvolvingCharacterIds.length > 0) requestBody.involving_character_ids = aiInvolvingCharacterIds;
            if (aiCausedByEventIds.length > 0) requestBody.caused_by_event_ids = aiCausedByEventIds;
            if (aiUserPrompt) requestBody.user_prompt = aiUserPrompt;
            if (aiProvider) requestBody.provider = aiProvider;
            if (aiModel) requestBody.model = aiModel;
            if (aiTemperature !== null) requestBody.temperature = aiTemperature;

            const response = await api.post<EventSuggestionsResponse>(
                `/worlds/${worldId}/events/generate`,
                requestBody
            );

            aiSuggestions = response.suggestions;
            showAIInputModal = false;
            showAIResultsModal = true;
        } catch (e: any) {
            aiError = e.message || "Failed to generate events";
        } finally {
            aiGenerating = false;
        }
    }

    async function createEventFromSuggestion(suggestion: EventSuggestion) {
        try {
            await api.post(`/worlds/${worldId}/events`, {
                t: suggestion.t,
                label_time: suggestion.label_time || null,
                type: suggestion.event_type,
                summary: suggestion.summary,
                description: suggestion.description,
                tags: suggestion.tags,
                location_id: null, // Would need to resolve location_hint to actual location
            });

            // Reload events
            const eventsData = await api.get<WorldEvent[]>(`/worlds/${worldId}/events`);
            events = eventsData.sort((a, b) => a.t - b.t);

            // Remove suggestion from list
            aiSuggestions = aiSuggestions.filter((s) => s !== suggestion);

            // Close modal if no more suggestions
            if (aiSuggestions.length === 0) {
                showAIResultsModal = false;
            }
        } catch (e: any) {
            alert(`Failed to create event: ${e.message}`);
        }
    }

    function toggleCharacterSelection(characterId: string) {
        if (aiInvolvingCharacterIds.includes(characterId)) {
            aiInvolvingCharacterIds = aiInvolvingCharacterIds.filter(id => id !== characterId);
        } else {
            aiInvolvingCharacterIds = [...aiInvolvingCharacterIds, characterId];
        }
    }

    function toggleEventSelection(eventId: string) {
        if (aiCausedByEventIds.includes(eventId)) {
            aiCausedByEventIds = aiCausedByEventIds.filter(id => id !== eventId);
        } else {
            aiCausedByEventIds = [...aiCausedByEventIds, eventId];
        }
    }

    // Event type options for UI
    const eventTypeOptions = [
        { value: "", label: "Any type" },
        { value: "battle", label: "Battle/Conflict" },
        { value: "discovery", label: "Discovery" },
        { value: "political", label: "Political" },
        { value: "natural", label: "Natural Event" },
        { value: "personal", label: "Personal Event" },
        { value: "catastrophe", label: "Catastrophe" },
        { value: "celebration", label: "Celebration" },
        { value: "migration", label: "Migration" },
    ];
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
                <div class="flex gap-3">
                    <button
                        on:click={openAIGenerationModal}
                        class="inline-flex items-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500"
                    >
                        <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                        Generate with AI
                    </button>
                    <a
                        href="/worlds/{worldId}/events/new"
                        class="inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                    >
                        + Create Event
                    </a>
                </div>
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
                <EventDependencyGraph worldId={worldId ?? ""} apiUrl={import.meta.env.VITE_API_URL} />
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

<!-- AI Generation Input Modal -->
{#if showAIInputModal}
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40"></div>
    <div class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
            <div class="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-2xl sm:p-6">
                <div class="absolute right-0 top-0 pr-4 pt-4">
                    <button
                        type="button"
                        class="rounded-md text-gray-400 hover:text-gray-500"
                        on:click={() => (showAIInputModal = false)}
                    >
                        <span class="sr-only">Close</span>
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div class="sm:flex sm:items-start">
                    <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-purple-100 sm:mx-0 sm:h-10 sm:w-10">
                        <svg class="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                        </svg>
                    </div>
                    <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left flex-1">
                        <h3 class="text-lg font-semibold leading-6 text-gray-900 dark:text-white">Generate World Events with AI</h3>
                        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            Configure AI generation parameters for canonical world events.
                        </p>
                    </div>
                </div>

                <form on:submit|preventDefault={generateWithAI} class="mt-6 space-y-4">
                    <!-- Event Type -->
                    <div>
                        <label for="event-type" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Event Type (optional)
                        </label>
                        <select
                            id="event-type"
                            bind:value={aiEventType}
                            class="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                        >
                            {#each eventTypeOptions as option}
                                <option value={option.value}>{option.label}</option>
                            {/each}
                        </select>
                    </div>

                    <!-- Time Range -->
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label for="time-min" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                Time Range Min (t)
                            </label>
                            <input
                                id="time-min"
                                type="number"
                                step="0.1"
                                bind:value={aiTimeRangeMin}
                                placeholder="e.g., 0"
                                class="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                            />
                        </div>
                        <div>
                            <label for="time-max" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                Time Range Max (t)
                            </label>
                            <input
                                id="time-max"
                                type="number"
                                step="0.1"
                                bind:value={aiTimeRangeMax}
                                placeholder="e.g., 100"
                                class="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                            />
                        </div>
                    </div>

                    <!-- Location -->
                    {#if locations.length > 0}
                        <div>
                            <label for="location" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                                Location (optional)
                            </label>
                            <select
                                id="location"
                                bind:value={aiLocationId}
                                class="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                            >
                                <option value="">Any location</option>
                                {#each locations as loc}
                                    <option value={loc.id}>{loc.name}</option>
                                {/each}
                            </select>
                        </div>
                    {/if}

                    <!-- Involved Characters -->
                    {#if characters.length > 0}
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Involved Characters (optional)
                            </label>
                            <div class="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border border-gray-200 dark:border-gray-600 rounded-md">
                                {#each characters as char}
                                    <button
                                        type="button"
                                        on:click={() => toggleCharacterSelection(char.id)}
                                        class="px-2 py-1 text-xs rounded-full transition-colors {aiInvolvingCharacterIds.includes(char.id) ? 'bg-purple-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'}"
                                    >
                                        {char.name}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    <!-- Caused By Events -->
                    {#if events.length > 0}
                        <div>
                            <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Caused By Events (optional)
                            </label>
                            <div class="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border border-gray-200 dark:border-gray-600 rounded-md">
                                {#each events as evt}
                                    <button
                                        type="button"
                                        on:click={() => toggleEventSelection(evt.id)}
                                        class="px-2 py-1 text-xs rounded-full transition-colors {aiCausedByEventIds.includes(evt.id) ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200'}"
                                    >
                                        t={evt.t}: {evt.summary.slice(0, 30)}{evt.summary.length > 30 ? '...' : ''}
                                    </button>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    <!-- User Prompt -->
                    <div>
                        <label for="user-prompt" class="block text-sm font-medium text-gray-700 dark:text-gray-300">
                            Additional Instructions (optional)
                        </label>
                        <textarea
                            id="user-prompt"
                            bind:value={aiUserPrompt}
                            rows="3"
                            placeholder="e.g., Focus on events that lead to the fall of the empire..."
                            class="mt-1 block w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm"
                        ></textarea>
                    </div>

                    <!-- AI Options -->
                    <AIGenerationOptions
                        bind:provider={aiProvider}
                        bind:model={aiModel}
                        bind:temperature={aiTemperature}
                        bind:expanded={aiOptionsExpanded}
                    />

                    {#if aiError}
                        <div class="rounded-md bg-red-50 dark:bg-red-900/50 p-4">
                            <p class="text-sm text-red-700 dark:text-red-300">{aiError}</p>
                        </div>
                    {/if}

                    <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse gap-3">
                        <button
                            type="submit"
                            disabled={aiGenerating}
                            class="inline-flex w-full justify-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 disabled:opacity-50 sm:w-auto"
                        >
                            {#if aiGenerating}
                                <svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Generating...
                            {:else}
                                Generate Events
                            {/if}
                        </button>
                        <button
                            type="button"
                            class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                            on:click={() => (showAIInputModal = false)}
                        >
                            Cancel
                        </button>
                    </div>
                </form>
            </div>
        </div>
    </div>
{/if}

<!-- AI Generation Results Modal -->
{#if showAIResultsModal && aiSuggestions.length > 0}
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40"></div>
    <div class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
            <div class="relative transform overflow-hidden rounded-lg bg-white dark:bg-gray-800 px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-4xl sm:p-6">
                <div class="absolute right-0 top-0 pr-4 pt-4">
                    <button
                        type="button"
                        class="rounded-md text-gray-400 hover:text-gray-500"
                        on:click={() => (showAIResultsModal = false)}
                    >
                        <span class="sr-only">Close</span>
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div class="sm:flex sm:items-start mb-6">
                    <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-green-100 sm:mx-0 sm:h-10 sm:w-10">
                        <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                        <h3 class="text-lg font-semibold leading-6 text-gray-900 dark:text-white">AI Event Suggestions</h3>
                        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                            {aiSuggestions.length} event{aiSuggestions.length !== 1 ? 's' : ''} generated. Click "Add" to create.
                        </p>
                    </div>
                </div>

                <div class="space-y-4 max-h-[60vh] overflow-y-auto">
                    {#each aiSuggestions as suggestion, i}
                        <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-purple-300 transition-colors">
                            <div class="flex items-start justify-between">
                                <div class="flex-1">
                                    <div class="flex items-center gap-2 mb-2">
                                        <span class="inline-flex items-center rounded-md bg-indigo-50 dark:bg-indigo-900/50 px-2 py-1 text-xs font-medium text-indigo-700 dark:text-indigo-300 ring-1 ring-inset ring-indigo-600/20">
                                            t = {suggestion.t}
                                        </span>
                                        {#if suggestion.label_time}
                                            <span class="inline-flex items-center rounded-md bg-gray-50 dark:bg-gray-700 px-2 py-1 text-xs font-medium text-gray-600 dark:text-gray-300">
                                                {suggestion.label_time}
                                            </span>
                                        {/if}
                                        <span class="inline-flex items-center rounded-md bg-purple-50 dark:bg-purple-900/50 px-2 py-1 text-xs font-medium text-purple-700 dark:text-purple-300 ring-1 ring-inset ring-purple-600/20">
                                            {suggestion.event_type}
                                        </span>
                                        <span class="text-xs text-gray-400">
                                            {Math.round(suggestion.confidence * 100)}% confidence
                                        </span>
                                    </div>

                                    <h4 class="text-sm font-semibold text-gray-900 dark:text-white">
                                        {suggestion.summary}
                                    </h4>

                                    <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">
                                        {suggestion.description}
                                    </p>

                                    {#if suggestion.location_hint}
                                        <p class="mt-2 text-xs text-gray-500">
                                            <span class="font-medium">Location hint:</span> {suggestion.location_hint}
                                        </p>
                                    {/if}

                                    {#if suggestion.involved_characters.length > 0}
                                        <p class="mt-1 text-xs text-gray-500">
                                            <span class="font-medium">Involves:</span> {suggestion.involved_characters.join(', ')}
                                        </p>
                                    {/if}

                                    {#if suggestion.caused_by_hints.length > 0}
                                        <p class="mt-1 text-xs text-gray-500">
                                            <span class="font-medium">Caused by:</span> {suggestion.caused_by_hints.join(', ')}
                                        </p>
                                    {/if}

                                    {#if suggestion.tags.length > 0}
                                        <div class="mt-2 flex flex-wrap gap-1">
                                            {#each suggestion.tags as tag}
                                                <span class="inline-flex items-center rounded-full bg-gray-100 dark:bg-gray-700 px-2 py-0.5 text-xs text-gray-600 dark:text-gray-400">
                                                    {tag}
                                                </span>
                                            {/each}
                                        </div>
                                    {/if}

                                    {#if suggestion.reasoning}
                                        <details class="mt-2">
                                            <summary class="text-xs text-gray-400 cursor-pointer hover:text-gray-500">
                                                AI reasoning
                                            </summary>
                                            <p class="mt-1 text-xs text-gray-500 italic">
                                                {suggestion.reasoning}
                                            </p>
                                        </details>
                                    {/if}
                                </div>

                                <button
                                    on:click={() => createEventFromSuggestion(suggestion)}
                                    class="ml-4 inline-flex items-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500"
                                >
                                    Add
                                </button>
                            </div>
                        </div>
                    {/each}
                </div>

                <div class="mt-6 flex justify-end gap-3">
                    <button
                        type="button"
                        class="inline-flex justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                        on:click={() => (showAIResultsModal = false)}
                    >
                        Close
                    </button>
                    <button
                        type="button"
                        class="inline-flex justify-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500"
                        on:click={() => {
                            showAIResultsModal = false;
                            openAIGenerationModal();
                        }}
                    >
                        Generate More
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}
