<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import { GenerationPanel, LoadingSpinner, BeatModificationPanel, DraggableBeatCard, BeatFilters, BeatSearch, StoryModePanel, AuthoringModeSelector } from "$lib/components";
    import StoryCoherenceChecker from "$lib/components/StoryCoherenceChecker.svelte";
    import StoryStatistics from "$lib/components/StoryStatistics.svelte";
    import type { Story, StoryBeat, BeatResponse, BeatReorderRequest } from "$lib/types";
    import { AUTHORING_MODE_LABELS, POV_TYPE_LABELS } from "$lib/types";
    import { dndzone } from 'svelte-dnd-action';
    import { flip } from 'svelte/animate';

    let story: Story | null = null;
    let beats: StoryBeat[] = [];
    let filteredBeats: StoryBeat[] = [];
    let searchedBeats: StoryBeat[] = [];
    let loading = true;
    let error = "";
    let modifyingBeat: StoryBeat | null = null;
    let reordering = false;

    $: storyId = $page.params.id;
    $: displayedBeats = searchedBeats.length > 0 || beats.length === 0 ? searchedBeats : beats;
    const flipDurationMs = 300;

    onMount(async () => {
        try {
            const [storyData, beatsData] = await Promise.all([
                api.get<Story>(`/stories/${storyId}`),
                api.get<StoryBeat[]>(`/stories/${storyId}/beats`),
            ]);
            story = storyData;
            beats = beatsData;
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    });

    async function handleDeleteBeat(beatId: string) {
        if (!confirm("Are you sure you want to delete this beat? This action cannot be undone.")) {
            return;
        }

        try {
            await api.delete(`/stories/${storyId}/beats/${beatId}`);
            // Reload the page to refresh the beats list
            window.location.reload();
        } catch (e: any) {
            alert(`Failed to delete beat: ${e.message}`);
        }
    }

    async function handleDeleteStory() {
        if (
            !confirm(
                "Are you sure you want to archive this story? You can restore it later from the archived stories page.",
            )
        ) {
            return;
        }

        try {
            const worldId = story?.world_id;
            await api.delete(`/stories/${storyId}`);
            goto(`/worlds/${worldId}`);
        } catch (e: any) {
            alert(`Failed to archive story: ${e.message}`);
        }
    }

    async function handleCloneStory() {
        if (!confirm("Create a copy of this story with all its beats?")) {
            return;
        }

        try {
            const clonedStory = await api.post<Story>(`/stories/${storyId}/clone`, {});
            goto(`/stories/${clonedStory.id}`);
        } catch (e: any) {
            alert(`Failed to clone story: ${e.message}`);
        }
    }

    async function handleRestoreStory() {
        try {
            await api.post(`/stories/${storyId}/restore`, {});
            window.location.reload();
        } catch (e: any) {
            alert(`Failed to restore story: ${e.message}`);
        }
    }

    function openModificationPanel(beat: StoryBeat) {
        modifyingBeat = beat;
    }

    function closeModificationPanel() {
        modifyingBeat = null;
    }

    function handleModificationApplied() {
        modifyingBeat = null;
        window.location.reload();
    }

    function handleDndConsider(e: CustomEvent<any>) {
        // Update local state immediately for smooth animation
        displayedBeats = e.detail.items;
    }

    async function handleDndFinalize(e: CustomEvent<any>) {
        // Get the new order
        const reorderedBeats = e.detail.items;
        displayedBeats = reorderedBeats;
        beats = reorderedBeats;

        // Call API to persist the new order
        reordering = true;
        try {
            const beatIds = reorderedBeats.map((b: StoryBeat) => b.id);
            const request: BeatReorderRequest = { beat_ids: beatIds };

            await api.post(`/stories/${storyId}/beats/reorder`, request);

            // Refresh beats to get updated order_index values
            const updatedBeats = await api.get<StoryBeat[]>(`/stories/${storyId}/beats`);
            beats = updatedBeats;
        } catch (err: any) {
            // Rollback on error
            beats = await api.get<StoryBeat[]>(`/stories/${storyId}/beats`);
            alert(`Failed to reorder beats: ${err.message}`);
        } finally {
            reordering = false;
        }
    }

    function handleFilterChange(filtered: StoryBeat[]) {
        filteredBeats = filtered;
        // Apply search on top of filters
        handleSearchChange(searchedBeats);
    }

    function handleSearchChange(searched: StoryBeat[]) {
        // Search works on the filtered beats
        const beatsToSearch = filteredBeats.length > 0 ? filteredBeats : beats;

        if (searched.length === 0 && beatsToSearch.length > 0) {
            // No search query - show all filtered beats
            searchedBeats = beatsToSearch;
        } else {
            // Search is active - only show matching beats from filtered set
            searchedBeats = searched.filter(beat =>
                beatsToSearch.some(b => b.id === beat.id)
            );
        }
    }

    function handleModeChange(newMode: string) {
        // Update local story state
        if (story) {
            story.mode = newMode as any;
        }
        // Reload page to refresh UI components with new mode
        window.location.reload();
    }
</script>

{#if loading}
    <div class="flex items-center justify-center py-12">
        <LoadingSpinner size="lg" text="Loading story..." />
    </div>
{:else if error}
    <div class="text-center py-12 text-red-500 dark:text-red-400">{error}</div>
{:else if story}
    <div class="space-y-8">
        <div class="border-b border-gray-200 dark:border-gray-700 pb-5">
            <div class="flex items-center justify-between mb-3">
                <h1 class="text-3xl font-bold leading-6 text-gray-900 dark:text-gray-100">
                    {story.title}
                </h1>
                <div class="flex items-center gap-3">
                    <span
                        class="inline-flex items-center rounded-full bg-green-50 dark:bg-green-900/30 px-2 py-1 text-xs font-medium text-green-700 dark:text-green-300 ring-1 ring-inset ring-green-600/20 dark:ring-green-500/30"
                        >{story.status}</span
                    >
                    {#if story.archived_at}
                        <span
                            class="inline-flex items-center rounded-full bg-yellow-50 dark:bg-yellow-900/30 px-2 py-1 text-xs font-medium text-yellow-700 dark:text-yellow-300 ring-1 ring-inset ring-yellow-600/20 dark:ring-yellow-500/30"
                        >
                            Archived
                        </span>
                    {/if}
                    {#if story.archived_at}
                        <button
                            on:click={handleRestoreStory}
                            class="inline-flex items-center rounded-md bg-green-600 dark:bg-green-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-green-500 dark:hover:bg-green-400"
                        >
                            Restore Story
                        </button>
                    {:else}
                        <a
                            href="/stories/{storyId}/edit"
                            class="inline-flex items-center rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
                        >
                            ✎ Edit
                        </a>
                        <button
                            on:click={handleCloneStory}
                            class="inline-flex items-center rounded-md bg-indigo-600 dark:bg-indigo-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400"
                        >
                            Clone
                        </button>
                        <button
                            on:click={handleDeleteStory}
                            class="inline-flex items-center rounded-md bg-orange-600 dark:bg-orange-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-orange-500 dark:hover:bg-orange-400"
                        >
                            Archive
                        </button>
                    {/if}
                </div>
            </div>
            <p class="mt-2 max-w-4xl text-sm text-gray-500 dark:text-gray-400">
                {story.synopsis || "No synopsis"}
            </p>
            <div class="mt-2 flex flex-wrap gap-2 items-center">
                {#if story.theme}
                    <span class="text-xs text-gray-400 dark:text-gray-500">Theme: {story.theme}</span>
                {/if}
                <span class="inline-flex items-center rounded-md bg-blue-50 dark:bg-blue-900/30 px-2 py-1 text-xs font-medium text-blue-700 dark:text-blue-300 ring-1 ring-inset ring-blue-600/20 dark:ring-blue-500/30">
                    {AUTHORING_MODE_LABELS[story.mode]}
                </span>
                <span class="inline-flex items-center rounded-md bg-purple-50 dark:bg-purple-900/30 px-2 py-1 text-xs font-medium text-purple-700 dark:text-purple-300 ring-1 ring-inset ring-purple-600/20 dark:ring-purple-500/30">
                    {POV_TYPE_LABELS[story.pov_type]}
                </span>
            </div>
            {#if story.tags && story.tags.length > 0}
                <div class="mt-3 flex flex-wrap gap-2">
                    {#each story.tags as tag}
                        <span class="inline-flex items-center rounded-full bg-indigo-100 dark:bg-indigo-900 px-3 py-1 text-xs font-medium text-indigo-700 dark:text-indigo-200">
                            {tag}
                        </span>
                    {/each}
                </div>
            {/if}
            <div class="mt-4">
                <a
                    href="/worlds/{story.world_id}"
                    class="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-500 dark:hover:text-indigo-300"
                    >← Back to World</a
                >
            </div>
        </div>

        <!-- Story Statistics -->
        {#if !story.archived_at}
            <div class="my-8">
                <StoryStatistics storyId={storyId ?? ""} />
            </div>
        {/if}

        <!-- Authoring Mode Selector -->
        <div class="mb-8">
            <AuthoringModeSelector
                currentMode={story.mode}
                storyId={storyId ?? ""}
                beatCount={beats.length}
                onChange={handleModeChange}
            />
        </div>

        <!-- Mode-Specific Help Panel -->
        <div class="mb-8">
            <StoryModePanel mode={story.mode} storyId={storyId ?? ""} beatCount={beats.length} />
        </div>

        <!-- Story Coherence Checker -->
        {#if beats.length > 0}
            <div class="mb-8">
                <StoryCoherenceChecker storyId={storyId ?? ""} />
            </div>
        {/if}

        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-xl font-semibold text-gray-900 dark:text-gray-100">Story Beats</h2>
                <a
                    href="/stories/{storyId}/beats/new"
                    class="inline-flex items-center rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
                >
                    + Create Beat Manually
                </a>
            </div>

            <div class="mb-8">
                <GenerationPanel
                    storyId={storyId ?? ""}
                    storyMode={story.mode}
                    onBeatGenerated={() => window.location.reload()}
                />
            </div>

            <!-- Filters and Search -->
            <div class="mb-6 space-y-4">
                <BeatSearch beats={filteredBeats.length > 0 ? filteredBeats : beats} onSearchChange={handleSearchChange} />
                <BeatFilters beats={beats} onFilterChange={handleFilterChange} />
            </div>

            <!-- Results Summary -->
            {#if displayedBeats.length !== beats.length}
                <div class="mb-4 text-sm text-gray-600 dark:text-gray-400 bg-indigo-50 dark:bg-indigo-900/30 px-4 py-2 rounded-md border border-indigo-100 dark:border-indigo-700">
                    Showing {displayedBeats.length} of {beats.length} beats
                </div>
            {/if}

            {#if reordering}
                <div class="flex items-center justify-center py-4">
                    <LoadingSpinner size="sm" text="Saving order..." />
                </div>
            {/if}

            <div
                class="space-y-4"
                use:dndzone={{ items: displayedBeats, flipDurationMs, dragDisabled: displayedBeats.length === 0, dropTargetStyle: {} }}
                on:consider={handleDndConsider}
                on:finalize={handleDndFinalize}
            >
                {#each displayedBeats as beat (beat.id)}
                    <div animate:flip={{ duration: flipDurationMs }}>
                        <DraggableBeatCard
                            {beat}
                            {storyId}
                            onModify={openModificationPanel}
                            onDelete={handleDeleteBeat}
                            onUpdate={() => window.location.reload()}
                        />
                    </div>
                {/each}

                {#if displayedBeats.length === 0}
                    <div
                        class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow border border-gray-200 dark:border-gray-700"
                    >
                        <p class="text-sm text-gray-500 dark:text-gray-400">
                            {#if beats.length === 0}
                                No beats yet. Use AI to generate ideas!
                            {:else}
                                No beats match your search/filter criteria.
                            {/if}
                        </p>
                    </div>
                {/if}
            </div>
        </div>
    </div>
{/if}

<!-- Modification Panel (Slide-in from Right) -->
{#if modifyingBeat}
    <!-- Backdrop -->
    <div
        class="fixed inset-0 bg-black/50 dark:bg-black/70 z-40 transition-opacity"
        on:click={closeModificationPanel}
        on:keydown={(e) => e.key === "Escape" && closeModificationPanel()}
        role="button"
        tabindex="0"
    ></div>

    <!-- Panel -->
    <div class="fixed right-0 top-0 bottom-0 w-full md:w-2/3 lg:w-1/2 max-w-4xl z-50 transform transition-transform duration-300">
        <BeatModificationPanel
            beat={modifyingBeat as BeatResponse}
            storyId={storyId ?? ""}
            onModificationApplied={handleModificationApplied}
            onClose={closeModificationPanel}
        />
    </div>
{/if}
