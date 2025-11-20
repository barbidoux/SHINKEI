<script lang="ts">
    import type { StoryBeat } from "$lib/types";

    export let beats: StoryBeat[] = [];
    export let onFilterChange: (filtered: StoryBeat[]) => void;

    // Filter states
    let selectedTypes: string[] = [];
    let eventFilter: "all" | "linked" | "unlinked" = "all";
    let showFilters = false;

    const beatTypes = [
        { value: "scene", label: "Scene", color: "indigo" },
        { value: "summary", label: "Summary", color: "purple" },
        { value: "note", label: "Note", color: "gray" },
    ];

    // Apply filters whenever filter state changes
    $: {
        applyFilters();
    }

    function applyFilters() {
        let filtered = [...beats];

        // Filter by beat type
        if (selectedTypes.length > 0) {
            filtered = filtered.filter((beat) =>
                selectedTypes.includes(beat.type),
            );
        }

        // Filter by event linkage
        if (eventFilter === "linked") {
            filtered = filtered.filter((beat) => beat.world_event_id !== null);
        } else if (eventFilter === "unlinked") {
            filtered = filtered.filter((beat) => beat.world_event_id === null);
        }

        onFilterChange(filtered);
    }

    function toggleType(type: string) {
        if (selectedTypes.includes(type)) {
            selectedTypes = selectedTypes.filter((t) => t !== type);
        } else {
            selectedTypes = [...selectedTypes, type];
        }
    }

    function clearFilters() {
        selectedTypes = [];
        eventFilter = "all";
    }

    $: hasActiveFilters = selectedTypes.length > 0 || eventFilter !== "all";
    $: activeFilterCount =
        selectedTypes.length + (eventFilter !== "all" ? 1 : 0);
</script>

<div class="beat-filters">
    <!-- Toggle Button -->
    <div class="flex items-center justify-between mb-4">
        <button
            on:click={() => (showFilters = !showFilters)}
            class="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
            <svg
                class="h-5 w-5 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
            </svg>
            Filters
            {#if activeFilterCount > 0}
                <span
                    class="inline-flex items-center justify-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800"
                >
                    {activeFilterCount}
                </span>
            {/if}
        </button>

        {#if hasActiveFilters}
            <button
                on:click={clearFilters}
                class="text-sm text-gray-500 hover:text-gray-700"
            >
                Clear all
            </button>
        {/if}
    </div>

    <!-- Filter Panel -->
    {#if showFilters}
        <div
            class="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4 mb-4"
        >
            <!-- Beat Type Filter -->
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Beat Type
                </label>
                <div class="flex flex-wrap gap-2">
                    {#each beatTypes as beatType}
                        <button
                            on:click={() => toggleType(beatType.value)}
                            class="px-3 py-1.5 rounded-md text-sm font-medium border transition-colors {selectedTypes.includes(
                                beatType.value,
                            )
                                ? `bg-${beatType.color}-100 border-${beatType.color}-300 text-${beatType.color}-700`
                                : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}"
                        >
                            <span class="flex items-center gap-1">
                                {#if selectedTypes.includes(beatType.value)}
                                    <svg
                                        class="h-4 w-4"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                    >
                                        <path
                                            fill-rule="evenodd"
                                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                            clip-rule="evenodd"
                                        />
                                    </svg>
                                {/if}
                                {beatType.label}
                            </span>
                        </button>
                    {/each}
                </div>
            </div>

            <!-- Event Linkage Filter -->
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    World Event Linkage
                </label>
                <div class="flex gap-2">
                    <button
                        on:click={() => (eventFilter = "all")}
                        class="px-3 py-1.5 rounded-md text-sm font-medium border transition-colors {eventFilter ===
                        'all'
                            ? 'bg-indigo-100 border-indigo-300 text-indigo-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}"
                    >
                        All Beats
                    </button>
                    <button
                        on:click={() => (eventFilter = "linked")}
                        class="px-3 py-1.5 rounded-md text-sm font-medium border transition-colors {eventFilter ===
                        'linked'
                            ? 'bg-indigo-100 border-indigo-300 text-indigo-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}"
                    >
                        <span class="flex items-center gap-1">
                            {#if eventFilter === "linked"}
                                <svg
                                    class="h-4 w-4"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                >
                                    <path
                                        fill-rule="evenodd"
                                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                        clip-rule="evenodd"
                                    />
                                </svg>
                            {/if}
                            Linked to Events
                        </span>
                    </button>
                    <button
                        on:click={() => (eventFilter = "unlinked")}
                        class="px-3 py-1.5 rounded-md text-sm font-medium border transition-colors {eventFilter ===
                        'unlinked'
                            ? 'bg-indigo-100 border-indigo-300 text-indigo-700'
                            : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}"
                    >
                        <span class="flex items-center gap-1">
                            {#if eventFilter === "unlinked"}
                                <svg
                                    class="h-4 w-4"
                                    fill="currentColor"
                                    viewBox="0 0 20 20"
                                >
                                    <path
                                        fill-rule="evenodd"
                                        d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                                        clip-rule="evenodd"
                                    />
                                </svg>
                            {/if}
                            Not Linked
                        </span>
                    </button>
                </div>
            </div>

            <!-- Active Filters Summary -->
            {#if hasActiveFilters}
                <div class="pt-3 border-t border-gray-200">
                    <div class="text-xs text-gray-500 mb-2">
                        Active filters:
                    </div>
                    <div class="flex flex-wrap gap-2">
                        {#each selectedTypes as type}
                            {@const beatType = beatTypes.find(
                                (bt) => bt.value === type,
                            )}
                            <span
                                class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200"
                            >
                                Type: {beatType?.label || type}
                                <button
                                    on:click={() => toggleType(type)}
                                    class="hover:text-indigo-900"
                                >
                                    <svg
                                        class="h-3 w-3"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                    >
                                        <path
                                            fill-rule="evenodd"
                                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                            clip-rule="evenodd"
                                        />
                                    </svg>
                                </button>
                            </span>
                        {/each}
                        {#if eventFilter !== "all"}
                            <span
                                class="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200"
                            >
                                {eventFilter === "linked"
                                    ? "Linked to events"
                                    : "Not linked"}
                                <button
                                    on:click={() => (eventFilter = "all")}
                                    class="hover:text-indigo-900"
                                >
                                    <svg
                                        class="h-3 w-3"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                    >
                                        <path
                                            fill-rule="evenodd"
                                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                                            clip-rule="evenodd"
                                        />
                                    </svg>
                                </button>
                            </span>
                        {/if}
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>

<style>
    .beat-filters {
        width: 100%;
    }

    /* Tailwind dynamic classes need to be safelisted or use inline styles */
    /* For simplicity, using fixed indigo colors for selected state */
</style>
