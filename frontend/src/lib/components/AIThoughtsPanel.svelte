<script lang="ts">
    import { api } from "$lib/api";
    import type { BeatResponse, BeatReasoningUpdate } from "$lib/types";

    export let beat: BeatResponse;
    export let onUpdate: () => void;

    let isExpanded = false;
    let isEditing = false;
    let editedReasoning = beat.generation_reasoning || "";
    let loading = false;
    let error = "";

    // Toggle panel expansion
    function toggleExpanded() {
        isExpanded = !isExpanded;
    }

    // Start editing mode
    function startEdit() {
        editedReasoning = beat.generation_reasoning || "";
        isEditing = true;
        error = "";
    }

    // Cancel editing
    function cancelEdit() {
        isEditing = false;
        editedReasoning = beat.generation_reasoning || "";
        error = "";
    }

    // Save edited reasoning
    async function saveReasoning() {
        loading = true;
        error = "";

        try {
            const update: BeatReasoningUpdate = {
                generation_reasoning: editedReasoning || undefined,
            };

            await api.patch(
                `/stories/${beat.story_id}/beats/${beat.id}/reasoning`,
                update
            );

            // Update local beat data
            beat.generation_reasoning = editedReasoning;
            isEditing = false;
            onUpdate();
        } catch (e: any) {
            error = e.message || "Failed to update AI thoughts";
        } finally {
            loading = false;
        }
    }

    // Delete reasoning
    async function deleteReasoning() {
        if (!confirm("Delete AI thoughts? This cannot be undone.")) {
            return;
        }

        loading = true;
        error = "";

        try {
            const update: BeatReasoningUpdate = {
                generation_reasoning: undefined,
            };

            await api.patch(
                `/stories/${beat.story_id}/beats/${beat.id}/reasoning`,
                update
            );

            // Update local beat data
            beat.generation_reasoning = undefined;
            editedReasoning = "";
            isEditing = false;
            onUpdate();
        } catch (e: any) {
            error = e.message || "Failed to delete AI thoughts";
        } finally {
            loading = false;
        }
    }

    // Determine if AI thoughts exist
    $: hasThoughts = Boolean(beat.generation_reasoning);
</script>

<div class="bg-white shadow-sm ring-1 ring-gray-900/5 rounded-lg overflow-hidden">
    <!-- Panel Header -->
    <button
        on:click={toggleExpanded}
        class="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
    >
        <div class="flex items-center gap-2">
            <svg
                class="w-5 h-5 text-indigo-600 transition-transform {isExpanded
                    ? 'rotate-90'
                    : ''}"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
            >
                <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 5l7 7-7 7"
                />
            </svg>
            <span class="text-sm font-semibold text-gray-900">
                AI Thoughts
            </span>
            {#if hasThoughts}
                <span
                    class="inline-flex items-center rounded-md bg-indigo-50 px-2 py-0.5 text-xs font-medium text-indigo-700"
                >
                    Available
                </span>
            {:else}
                <span
                    class="inline-flex items-center rounded-md bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600"
                >
                    None
                </span>
            {/if}
        </div>
        <svg
            class="w-5 h-5 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
        >
            <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
        </svg>
    </button>

    <!-- Panel Content -->
    {#if isExpanded}
        <div class="border-t border-gray-200 p-4">
            {#if !hasThoughts && !isEditing}
                <!-- Empty State -->
                <div class="text-center py-6">
                    <svg
                        class="mx-auto h-12 w-12 text-gray-400"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                        />
                    </svg>
                    <p class="mt-2 text-sm text-gray-500">
                        No AI thoughts available for this beat.
                    </p>
                    <p class="mt-1 text-xs text-gray-400">
                        AI thoughts are generated automatically when using AI generation.
                    </p>
                </div>
            {:else if isEditing}
                <!-- Edit Mode -->
                <div class="space-y-3">
                    <label
                        for="reasoning-edit"
                        class="block text-xs font-medium text-gray-700"
                    >
                        Edit AI Reasoning
                    </label>
                    <textarea
                        id="reasoning-edit"
                        bind:value={editedReasoning}
                        rows="6"
                        placeholder="Enter AI reasoning or thoughts about this beat..."
                        class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
                    ></textarea>

                    {#if error}
                        <div class="rounded-md bg-red-50 p-3">
                            <p class="text-xs text-red-800">{error}</p>
                        </div>
                    {/if}

                    <div class="flex justify-end gap-2">
                        <button
                            on:click={cancelEdit}
                            disabled={loading}
                            class="rounded-md bg-white px-3 py-1.5 text-xs font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 disabled:opacity-50"
                        >
                            Cancel
                        </button>
                        <button
                            on:click={saveReasoning}
                            disabled={loading}
                            class="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
                        >
                            {loading ? "Saving..." : "Save"}
                        </button>
                    </div>
                </div>
            {:else}
                <!-- Display Mode -->
                <div class="space-y-3">
                    <div
                        class="rounded-md bg-indigo-50 p-3 border border-indigo-200"
                    >
                        <p class="text-sm text-gray-700 whitespace-pre-wrap">
                            {beat.generation_reasoning}
                        </p>
                    </div>

                    {#if error}
                        <div class="rounded-md bg-red-50 p-3">
                            <p class="text-xs text-red-800">{error}</p>
                        </div>
                    {/if}

                    <div class="flex justify-between items-center">
                        <p class="text-xs text-gray-500">
                            AI's reasoning process behind this beat
                        </p>
                        <div class="flex gap-2">
                            <button
                                on:click={startEdit}
                                disabled={loading}
                                class="text-xs font-medium text-indigo-600 hover:text-indigo-500 disabled:opacity-50"
                            >
                                Edit
                            </button>
                            <button
                                on:click={deleteReasoning}
                                disabled={loading}
                                class="text-xs font-medium text-red-600 hover:text-red-500 disabled:opacity-50"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            {/if}
        </div>
    {/if}
</div>
