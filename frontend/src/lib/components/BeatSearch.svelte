<script lang="ts">
    import type { StoryBeat } from "$lib/types";

    export let beats: StoryBeat[] = [];
    export let onSearchChange: (filtered: StoryBeat[]) => void;

    let searchQuery = "";
    let searchFields: string[] = ["content", "summary", "time_label"];

    const searchFieldOptions = [
        { value: "content", label: "Content" },
        { value: "summary", label: "Summary" },
        { value: "time_label", label: "Time Label" },
    ];

    // Apply search whenever query or fields change
    $: {
        applySearch();
    }

    function applySearch() {
        if (!searchQuery.trim()) {
            onSearchChange(beats);
            return;
        }

        const query = searchQuery.toLowerCase().trim();
        const filtered = beats.filter((beat) => {
            // Check content
            if (
                searchFields.includes("content") &&
                beat.content?.toLowerCase().includes(query)
            ) {
                return true;
            }

            // Check summary
            if (
                searchFields.includes("summary") &&
                beat.summary?.toLowerCase().includes(query)
            ) {
                return true;
            }

            // Check time label
            if (
                searchFields.includes("time_label") &&
                beat.local_time_label?.toLowerCase().includes(query)
            ) {
                return true;
            }

            return false;
        });

        onSearchChange(filtered);
    }

    function toggleSearchField(field: string) {
        if (searchFields.includes(field)) {
            // Don't allow removing all fields
            if (searchFields.length > 1) {
                searchFields = searchFields.filter((f) => f !== field);
            }
        } else {
            searchFields = [...searchFields, field];
        }
    }

    function clearSearch() {
        searchQuery = "";
        searchFields = ["content", "summary", "time_label"];
    }
</script>

<div class="beat-search">
    <!-- Search Input -->
    <div class="relative">
        <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
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
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
            </svg>
        </div>
        <input
            type="text"
            bind:value={searchQuery}
            placeholder="Search beats..."
            class="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
        />
        {#if searchQuery}
            <div class="absolute inset-y-0 right-0 pr-3 flex items-center">
                <button
                    on:click={clearSearch}
                    class="text-gray-400 hover:text-gray-500"
                >
                    <svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                            fill-rule="evenodd"
                            d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                            clip-rule="evenodd"
                        />
                    </svg>
                </button>
            </div>
        {/if}
    </div>

    <!-- Search Fields Toggle -->
    <div class="mt-2">
        <div class="flex items-center gap-2 text-xs">
            <span class="text-gray-500">Search in:</span>
            {#each searchFieldOptions as option}
                <button
                    on:click={() => toggleSearchField(option.value)}
                    class="px-2 py-1 rounded-md font-medium transition-colors {searchFields.includes(
                        option.value,
                    )
                        ? 'bg-indigo-100 text-indigo-700 border border-indigo-200'
                        : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'}"
                >
                    {option.label}
                </button>
            {/each}
        </div>
    </div>

    <!-- Search Results Summary -->
    {#if searchQuery}
        <div class="mt-2 text-xs text-gray-500">
            {#if beats.length === 0}
                No beats to search
            {:else}
                <span>
                    Searching {beats.length}
                    {beats.length === 1 ? "beat" : "beats"}
                </span>
            {/if}
        </div>
    {/if}
</div>

<style>
    .beat-search {
        width: 100%;
    }
</style>
