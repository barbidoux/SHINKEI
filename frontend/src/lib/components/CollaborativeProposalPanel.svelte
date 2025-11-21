<script lang="ts">
    import { api } from "$lib/api";
    import WorldEventPicker from "./WorldEventPicker.svelte";

    export let storyId: string;
    export let worldId: string; // World ID for loading events
    export let onProposalUsed: () => void;

    interface BeatProposal {
        id: string;
        content: string;
        summary: string;
        local_time_label: string;
        beat_type: string;
        reasoning?: string;
    }

    interface ExistingBeat {
        id: string;
        order_index: number;
        summary: string | null;
        content: string;
    }

    let userGuidance: string = "";
    let proposals: BeatProposal[] = [];
    let selectedIndex: number | null = null;
    let generating: boolean = false;
    let error: string = "";
    let expandedReasoning: { [key: number]: boolean } = {};
    let expandedContent: { [key: number]: boolean } = {};
    let generatingProgress: number = 0; // Total count of completed proposals
    let proposalSlots: (BeatProposal | null)[] = [null, null, null]; // Track which slots are filled

    // Proposal editing state
    let editingProposalIndex: number | null = null;
    let editedContent: string = "";
    let editedMetadata: {
        beat_type: string;
        summary: string;
        local_time_label: string;
        world_event_id: string;
    } = {
        beat_type: "",
        summary: "",
        local_time_label: "",
        world_event_id: ""
    };

    // Beat insertion controls
    let insertionMode: string = "append"; // "append" | "insert_after" | "insert_at"
    let insertAfterBeatId: string = "";
    let insertAtPosition: number = 1;
    let existingBeats: ExistingBeat[] = [];
    let loadingBeats: boolean = false;

    // Advanced metadata control options
    let showAdvancedOptions: boolean = false;
    let beatTypeMode: string = "automatic"; // "blank" | "manual" | "automatic"
    let beatTypeManual: string = "scene";
    let summaryMode: string = "automatic";
    let summaryManual: string = "";
    let localTimeLabelMode: string = "automatic";
    let localTimeLabelManual: string = "";
    let worldEventIdMode: string = "automatic";
    let worldEventIdManual: string = "";

    async function loadExistingBeats() {
        loadingBeats = true;
        try {
            const beats = await api.get<ExistingBeat[]>(`/stories/${storyId}/beats`);
            existingBeats = beats.sort((a, b) => a.order_index - b.order_index);
        } catch (e: any) {
            console.error("Failed to load beats:", e);
            existingBeats = [];
        } finally {
            loadingBeats = false;
        }
    }

    // Load beats when component mounts
    loadExistingBeats();

    async function generateProposals() {
        if (generating) return;

        generating = true;
        error = "";
        proposals = [];
        selectedIndex = null;
        generatingProgress = 0;
        proposalSlots = [null, null, null]; // Reset slots

        try {
            // Use streaming endpoint for real-time feedback
            const token = localStorage.getItem('auth')
                ? JSON.parse(localStorage.getItem('auth')!).token
                : null;

            if (!token) {
                throw new Error('Not authenticated');
            }

            const response = await fetch(
                `http://localhost:8000/api/v1/narrative/stories/${storyId}/beats/propose/stream`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        user_guidance: userGuidance || null,
                        num_proposals: 3,
                        provider: null,
                        insertion_mode: insertionMode,
                        insert_after_beat_id: insertionMode === "insert_after" ? insertAfterBeatId : null,
                        insert_at_position: insertionMode === "insert_at" ? insertAtPosition : null,
                        // Metadata controls
                        beat_type_mode: beatTypeMode,
                        beat_type_manual: beatTypeMode === "manual" ? beatTypeManual : null,
                        summary_mode: summaryMode,
                        summary_manual: summaryMode === "manual" ? summaryManual : null,
                        local_time_label_mode: localTimeLabelMode,
                        local_time_label_manual: localTimeLabelMode === "manual" ? localTimeLabelManual : null,
                        world_event_id_mode: worldEventIdMode,
                        world_event_id_manual: worldEventIdMode === "manual" ? worldEventIdManual : null
                    })
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('No response body');
            }

            // Read the stream
            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    break;
                }

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'proposal') {
                            // Add proposal to designated slot
                            proposalSlots[data.index] = data.proposal;
                            proposalSlots = [...proposalSlots]; // Trigger reactivity

                            // Calculate progress from filled slots
                            generatingProgress = proposalSlots.filter(p => p !== null).length;
                        } else if (data.type === 'error') {
                            console.error('Proposal generation error:', data.message);
                        }
                    }
                }
            }

            // Convert slots to final proposals array
            proposals = proposalSlots.filter(p => p !== null) as BeatProposal[];

        } catch (e: any) {
            error = e.message || "Failed to generate proposals";
            console.error("Proposal generation failed:", e);
        } finally {
            generating = false;
            generatingProgress = 0;
        }
    }

    function startEditingProposal(index: number) {
        editingProposalIndex = index;
        const proposal = proposals[index];
        editedContent = proposal.content;
        editedMetadata = {
            beat_type: proposal.beat_type,
            summary: proposal.summary,
            local_time_label: proposal.local_time_label,
            world_event_id: "" // Proposals don't have world_event_id yet
        };
    }

    function cancelEditingProposal() {
        editingProposalIndex = null;
        editedContent = "";
        editedMetadata = {
            beat_type: "",
            summary: "",
            local_time_label: "",
            world_event_id: ""
        };
    }

    async function useProposal(proposal: BeatProposal, useEditedVersion: boolean = false) {
        if (generating) return;

        generating = true;
        error = "";

        try {
            // Use edited content and metadata if in edit mode, otherwise use original
            const metadata = useEditedVersion && editingProposalIndex !== null ? {
                content: editedContent,
                summary: editedMetadata.summary,
                local_time_label: editedMetadata.local_time_label,
                beat_type: editedMetadata.beat_type,
                world_event_id: editedMetadata.world_event_id || null,
                generated_by: "collaborative"
            } : {
                content: proposal.content,
                summary: proposal.summary,
                local_time_label: proposal.local_time_label,
                beat_type: proposal.beat_type,
                generated_by: "collaborative"
            };

            // Create actual beat from proposal
            await api.post(`/stories/${storyId}/beats`, metadata);

            // Notify parent to reload
            onProposalUsed();

            // Reset state
            proposals = [];
            selectedIndex = null;
            userGuidance = "";
            editingProposalIndex = null;
            editedContent = "";
        } catch (e: any) {
            error = e.message || "Failed to create beat from proposal";
            console.error("Beat creation failed:", e);
        } finally {
            generating = false;
        }
    }

    function toggleReasoning(index: number) {
        expandedReasoning[index] = !expandedReasoning[index];
        expandedReasoning = { ...expandedReasoning }; // Trigger reactivity
    }

    function toggleContent(index: number) {
        expandedContent[index] = !expandedContent[index];
        expandedContent = { ...expandedContent }; // Trigger reactivity
    }

    function truncateContent(content: string, maxLength: number = 200): string {
        if (content.length <= maxLength) return content;
        return content.slice(0, maxLength) + "...";
    }

    function shouldShowExpandButton(content: string, maxLength: number = 300): boolean {
        return content.length > maxLength;
    }
</script>

<div class="collaborative-proposal-panel">
    <div class="mb-6 p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border-2 border-purple-200 dark:border-purple-700">
        <div class="flex items-center gap-2 mb-2">
            <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h4 class="text-sm font-semibold text-purple-900 dark:text-purple-100">
                Collaborative Mode Active
            </h4>
        </div>
        <p class="text-xs text-purple-700 dark:text-purple-300">
            Provide optional guidance, then review 3 AI-generated variations and select your favorite.
        </p>
    </div>

    <!-- User Guidance Input -->
    <div class="mb-6">
        <label for="user-guidance" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Your Guidance <span class="text-gray-500 dark:text-gray-400">(Optional)</span>
        </label>
        <textarea
            id="user-guidance"
            bind:value={userGuidance}
            placeholder="E.g., 'Make it more suspenseful' or 'Focus on character emotions' or 'Advance the mystery subplot'..."
            disabled={generating}
            class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-purple-500 dark:focus:ring-purple-400 disabled:opacity-50 disabled:bg-gray-50 dark:disabled:bg-gray-800"
            rows="3"
            maxlength="2000"
        ></textarea>
        <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {userGuidance.length}/2000 characters
        </p>
    </div>

    <!-- Beat Position Controls -->
    <div class="mb-6">
        <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Insert Position
        </label>
        <div class="space-y-3">
            <!-- Insertion mode selector -->
            <div class="flex gap-2">
                <button
                    type="button"
                    on:click={() => insertionMode = "append"}
                    class="flex-1 px-3 py-2 text-sm rounded-md border {insertionMode === 'append' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'}"
                >
                    📄 End of story
                </button>
                <button
                    type="button"
                    on:click={() => insertionMode = "insert_after"}
                    class="flex-1 px-3 py-2 text-sm rounded-md border {insertionMode === 'insert_after' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'}"
                >
                    ➡️ After beat
                </button>
                <button
                    type="button"
                    on:click={() => insertionMode = "insert_at"}
                    class="flex-1 px-3 py-2 text-sm rounded-md border {insertionMode === 'insert_at' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600'}"
                >
                    #️⃣ At position
                </button>
            </div>

            <!-- Insert after beat selector -->
            {#if insertionMode === "insert_after"}
                <select
                    bind:value={insertAfterBeatId}
                    class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-purple-500 dark:focus:ring-purple-400"
                >
                    <option value="">Select a beat...</option>
                    {#each existingBeats as beat}
                        <option value={beat.id}>
                            Beat #{beat.order_index}: {beat.summary || beat.content.substring(0, 50)}...
                        </option>
                    {/each}
                </select>
                {#if loadingBeats}
                    <p class="text-xs text-gray-500 dark:text-gray-400">Loading beats...</p>
                {:else if existingBeats.length === 0}
                    <p class="text-xs text-amber-600 dark:text-amber-400">No existing beats. Will insert at beginning.</p>
                {/if}
            {/if}

            <!-- Insert at position input -->
            {#if insertionMode === "insert_at"}
                <div class="flex items-center gap-2">
                    <input
                        type="number"
                        bind:value={insertAtPosition}
                        min="1"
                        max={existingBeats.length + 1}
                        class="flex-1 rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-purple-500 dark:focus:border-purple-400 focus:ring-purple-500 dark:focus:ring-purple-400"
                    />
                    <span class="text-sm text-gray-500 dark:text-gray-400">
                        (1 to {existingBeats.length + 1})
                    </span>
                </div>
                <p class="text-xs text-gray-500 dark:text-gray-400">
                    Position 1 = first beat, {existingBeats.length + 1} = last beat
                </p>
            {/if}
        </div>
    </div>

    <!-- Advanced Metadata Options -->
    <div class="mb-6">
        <button
            type="button"
            on:click={() => showAdvancedOptions = !showAdvancedOptions}
            class="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-purple-600 dark:hover:text-purple-400"
        >
            <svg class="w-4 h-4 transition-transform {showAdvancedOptions ? 'rotate-90' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
            Advanced Metadata Options
        </button>

        {#if showAdvancedOptions}
            <div class="mt-4 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700 space-y-4">
                <p class="text-xs text-gray-600 dark:text-gray-400 mb-3">
                    Control how metadata fields are determined for generated beats.
                </p>

                <!-- Beat Type Control -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Beat Type
                    </label>
                    <div class="flex gap-2 mb-2">
                        <button
                            type="button"
                            on:click={() => beatTypeMode = "automatic"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {beatTypeMode === 'automatic' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            🤖 AI Determines
                        </button>
                        <button
                            type="button"
                            on:click={() => beatTypeMode = "manual"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {beatTypeMode === 'manual' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ✏️ Manual
                        </button>
                        <button
                            type="button"
                            on:click={() => beatTypeMode = "blank"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {beatTypeMode === 'blank' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ⊘ Leave Blank
                        </button>
                    </div>
                    {#if beatTypeMode === "manual"}
                        <select
                            bind:value={beatTypeManual}
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                        >
                            <option value="scene">Scene</option>
                            <option value="summary">Summary</option>
                            <option value="note">Note</option>
                        </select>
                    {/if}
                </div>

                <!-- Summary Control -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Summary
                    </label>
                    <div class="flex gap-2 mb-2">
                        <button
                            type="button"
                            on:click={() => summaryMode = "automatic"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {summaryMode === 'automatic' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            🤖 AI Determines
                        </button>
                        <button
                            type="button"
                            on:click={() => summaryMode = "manual"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {summaryMode === 'manual' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ✏️ Manual
                        </button>
                        <button
                            type="button"
                            on:click={() => summaryMode = "blank"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {summaryMode === 'blank' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ⊘ Leave Blank
                        </button>
                    </div>
                    {#if summaryMode === "manual"}
                        <input
                            type="text"
                            bind:value={summaryManual}
                            placeholder="Enter summary text..."
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                        />
                    {/if}
                </div>

                <!-- Time Label Control -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Time Label
                    </label>
                    <div class="flex gap-2 mb-2">
                        <button
                            type="button"
                            on:click={() => localTimeLabelMode = "automatic"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {localTimeLabelMode === 'automatic' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            🤖 AI Determines
                        </button>
                        <button
                            type="button"
                            on:click={() => localTimeLabelMode = "manual"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {localTimeLabelMode === 'manual' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ✏️ Manual
                        </button>
                        <button
                            type="button"
                            on:click={() => localTimeLabelMode = "blank"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {localTimeLabelMode === 'blank' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ⊘ Leave Blank
                        </button>
                    </div>
                    {#if localTimeLabelMode === "manual"}
                        <input
                            type="text"
                            bind:value={localTimeLabelManual}
                            placeholder="E.g., 'Log 0042', 'Day 7, 14:00'..."
                            class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                        />
                    {/if}
                </div>

                <!-- World Event Control -->
                <div>
                    <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        World Event Link
                    </label>
                    <div class="flex gap-2 mb-2">
                        <button
                            type="button"
                            on:click={() => worldEventIdMode = "automatic"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {worldEventIdMode === 'automatic' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            🤖 AI Determines
                        </button>
                        <button
                            type="button"
                            on:click={() => worldEventIdMode = "manual"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {worldEventIdMode === 'manual' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ✏️ Manual
                        </button>
                        <button
                            type="button"
                            on:click={() => worldEventIdMode = "blank"}
                            class="flex-1 px-3 py-2 text-xs rounded-md border {worldEventIdMode === 'blank' ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-500 dark:border-purple-400 text-purple-900 dark:text-purple-100' : 'bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300'}"
                        >
                            ⊘ No Link
                        </button>
                    </div>
                    {#if worldEventIdMode === "manual"}
                        <WorldEventPicker
                            {worldId}
                            bind:selectedEventId={worldEventIdManual}
                            onSelect={(eventId) => worldEventIdManual = eventId}
                        />
                    {/if}
                </div>
            </div>
        {/if}
    </div>

    <!-- Generate Button -->
    <button
        on:click={generateProposals}
        disabled={generating}
        class="w-full mb-6 inline-flex items-center justify-center gap-2 rounded-md bg-purple-600 dark:bg-purple-500 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-purple-500 dark:hover:bg-purple-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-600 dark:focus-visible:outline-purple-400 disabled:opacity-50 disabled:cursor-not-allowed"
    >
        {#if generating}
            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Generating ({generatingProgress}/3)
        {:else}
            🤝 Generate Proposals
        {/if}
    </button>

    <!-- Live Generation Progress -->
    {#if generating}
        <div class="space-y-4 mb-6">
            <div class="flex items-center gap-2 mb-4">
                <div class="flex gap-1">
                    {#each [1, 2, 3] as i}
                        <div class="h-2 w-2 rounded-full {i <= generatingProgress ? 'bg-purple-600 dark:bg-purple-400' : 'bg-gray-300 dark:bg-gray-600'} transition-colors"></div>
                    {/each}
                </div>
                <p class="text-xs text-purple-700 dark:text-purple-300 font-medium">
                    {generatingProgress === 3 ? 'All proposals generated!' : `Generating proposal ${generatingProgress + 1} of 3...`}
                </p>
            </div>

            <!-- Show proposals as they arrive -->
            {#each [0, 1, 2] as i}
                {#if proposalSlots[i] !== null}
                    <!-- Real proposal card with appear animation -->
                    {@const proposal = proposalSlots[i]}
                    {@const isContentExpanded = expandedContent[i] === true}

                    <div class="rounded-lg border-2 border-purple-400 dark:border-purple-500 bg-purple-50 dark:bg-purple-900/20 p-4 transition-all animate-slideIn">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="inline-flex items-center rounded-full bg-purple-100 dark:bg-purple-900/50 px-2.5 py-0.5 text-xs font-medium text-purple-800 dark:text-purple-200">
                                Option {i + 1}
                            </span>
                            <svg class="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                            <span class="text-xs text-green-600 dark:text-green-400 font-medium">Ready</span>
                        </div>

                        <!-- Summary -->
                        <h5 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                            {proposal.summary}
                        </h5>

                        <!-- Content Preview -->
                        <div class="mb-2">
                            <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap {isContentExpanded ? '' : 'line-clamp-3'}">
                                {isContentExpanded ? proposal.content : truncateContent(proposal.content, 150)}
                            </p>
                            {#if shouldShowExpandButton(proposal.content, 150)}
                                <button
                                    type="button"
                                    on:click={() => toggleContent(i)}
                                    class="mt-1 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-500 dark:hover:text-purple-300"
                                >
                                    {isContentExpanded ? "▲ Show less" : "▼ Read more"}
                                </button>
                            {/if}
                        </div>
                    </div>
                {:else}
                    <!-- Skeleton loader for pending proposals -->
                    {@const isGenerating = proposalSlots.filter(p => p !== null).length > i}
                    <div class="rounded-lg border-2 border-dashed {isGenerating ? 'border-purple-400 dark:border-purple-500 bg-purple-50 dark:bg-purple-900/20' : 'border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'} p-4 transition-all">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="inline-flex items-center rounded-full bg-purple-100 dark:bg-purple-900/50 px-2.5 py-0.5 text-xs font-medium text-purple-800 dark:text-purple-200">
                                Option {i + 1}
                            </span>
                            {#if isGenerating}
                                <svg class="animate-spin h-4 w-4 text-purple-600 dark:text-purple-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                <span class="text-xs text-purple-600 dark:text-purple-400 font-medium">Crafting narrative...</span>
                            {:else}
                                <span class="text-xs text-gray-500 dark:text-gray-400">Waiting...</span>
                            {/if}
                        </div>

                        <!-- Skeleton animation -->
                        <div class="space-y-2 {isGenerating ? 'animate-pulse' : ''}">
                            <div class="h-3 {isGenerating ? 'bg-purple-200 dark:bg-purple-800' : 'bg-gray-200 dark:bg-gray-700'} rounded w-3/4"></div>
                            <div class="h-3 {isGenerating ? 'bg-purple-200 dark:bg-purple-800' : 'bg-gray-200 dark:bg-gray-700'} rounded w-full"></div>
                            <div class="h-3 {isGenerating ? 'bg-purple-200 dark:bg-purple-800' : 'bg-gray-200 dark:bg-gray-700'} rounded w-5/6"></div>
                        </div>
                    </div>
                {/if}
            {/each}
        </div>
    {/if}

    <!-- Error Display -->
    {#if error}
        <div class="mb-6 rounded-md bg-red-50 dark:bg-red-900/30 p-4 border border-red-200 dark:border-red-700">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400 dark:text-red-500" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm font-medium text-red-800 dark:text-red-300">{error}</p>
                </div>
            </div>
        </div>
    {/if}

    <!-- Proposals Display -->
    {#if proposals.length > 0 && !generating}
        <div class="space-y-4 mb-6">
            <div class="flex items-center gap-2 mb-2">
                <svg class="w-5 h-5 text-purple-600 dark:text-purple-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
                </svg>
                <h4 class="text-sm font-medium text-gray-900 dark:text-gray-100">
                    Select a Proposal ({proposals.length} options)
                </h4>
            </div>

            {#each proposals as proposal, i}
                {@const isSelected = selectedIndex === i}
                {@const isReasoningExpanded = expandedReasoning[i] === true}
                {@const isContentExpanded = expandedContent[i] === true}
                {@const isEditing = editingProposalIndex === i}

                <div
                    class="proposal-card relative rounded-lg border-2 p-4 transition-all {isSelected
                        ? 'border-purple-500 dark:border-purple-400 bg-purple-50 dark:bg-purple-900/30 shadow-md'
                        : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 hover:shadow-sm'}"
                >
                    <!-- Header -->
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex items-center gap-2 flex-1">
                            <span class="inline-flex items-center rounded-full bg-purple-100 dark:bg-purple-900/50 px-2.5 py-0.5 text-xs font-medium text-purple-800 dark:text-purple-200">
                                Option {i + 1}
                            </span>
                            {#if isEditing}
                                <span class="inline-flex items-center rounded-full bg-amber-100 dark:bg-amber-900/50 px-2.5 py-0.5 text-xs font-medium text-amber-800 dark:text-amber-200">
                                    ✏️ Editing
                                </span>
                            {:else}
                                <span class="text-xs text-gray-500 dark:text-gray-400">
                                    {proposal.beat_type} · {proposal.local_time_label}
                                </span>
                            {/if}
                        </div>

                        <!-- Select Radio Button -->
                        {#if !isEditing}
                            <input
                                type="radio"
                                name="proposal-selection"
                                checked={isSelected}
                                on:change={() => (selectedIndex = i)}
                                class="h-4 w-4 border-gray-300 text-purple-600 focus:ring-purple-600"
                            />
                        {/if}
                    </div>

                    <!-- Editable Content and Metadata (when editing) -->
                    {#if isEditing}
                        <div class="space-y-3 mb-4 p-3 bg-amber-50 dark:bg-amber-900/10 rounded-md border border-amber-200 dark:border-amber-800">
                            <!-- Content Editor -->
                            <div>
                                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Narrative Content
                                </label>
                                <textarea
                                    bind:value={editedContent}
                                    rows="8"
                                    class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm font-mono"
                                    placeholder="Edit the narrative content..."
                                ></textarea>
                                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                    {editedContent.length} characters
                                </p>
                            </div>

                            <!-- Divider -->
                            <div class="border-t border-amber-200 dark:border-amber-800 my-2"></div>

                            <!-- Metadata Fields -->
                            <div>
                                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Beat Type
                                </label>
                                <select
                                    bind:value={editedMetadata.beat_type}
                                    class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                                >
                                    <option value="scene">Scene</option>
                                    <option value="summary">Summary</option>
                                    <option value="note">Note</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Summary
                                </label>
                                <input
                                    type="text"
                                    bind:value={editedMetadata.summary}
                                    class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                                />
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    Time Label
                                </label>
                                <input
                                    type="text"
                                    bind:value={editedMetadata.local_time_label}
                                    class="w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                                />
                            </div>
                            <div>
                                <label class="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
                                    World Event Link (Optional)
                                </label>
                                <WorldEventPicker
                                    {worldId}
                                    bind:selectedEventId={editedMetadata.world_event_id}
                                    onSelect={(eventId) => editedMetadata.world_event_id = eventId}
                                />
                            </div>
                        </div>
                    {:else}
                        <!-- Summary (read-only when not editing) -->
                        <h5 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
                            {proposal.summary}
                        </h5>
                    {/if}

                    <!-- Content Preview with Expand/Collapse -->
                    <div class="mb-3">
                        <p class="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap {isContentExpanded ? '' : 'line-clamp-6'}">
                            {isContentExpanded ? proposal.content : truncateContent(proposal.content, 300)}
                        </p>

                        {#if shouldShowExpandButton(proposal.content, 300)}
                            <button
                                type="button"
                                on:click={() => toggleContent(i)}
                                class="mt-2 text-xs text-purple-600 dark:text-purple-400 hover:text-purple-500 dark:hover:text-purple-300 font-medium"
                            >
                                {isContentExpanded ? "▲ Show less" : "▼ Read full content"}
                            </button>
                        {/if}
                    </div>

                    <!-- AI Reasoning (Collapsible) -->
                    {#if proposal.reasoning}
                        <button
                            type="button"
                            on:click={() => toggleReasoning(i)}
                            class="text-xs text-purple-600 dark:text-purple-400 hover:text-purple-500 dark:hover:text-purple-300 font-medium mb-2"
                        >
                            {isReasoningExpanded ? "▼" : "▶"} AI Reasoning
                        </button>

                        {#if isReasoningExpanded}
                            <div class="bg-gray-50 dark:bg-gray-900/50 rounded p-3 text-xs text-gray-600 dark:text-gray-300 mb-3">
                                {proposal.reasoning}
                            </div>
                        {/if}
                    {/if}

                    <!-- Action Buttons -->
                    <div class="flex gap-2">
                        {#if isEditing}
                            <!-- Edit Mode Buttons -->
                            <button
                                on:click={() => useProposal(proposal, true)}
                                disabled={generating}
                                class="flex-1 inline-flex items-center justify-center gap-1 rounded-md bg-green-600 dark:bg-green-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-green-500 dark:hover:bg-green-400 disabled:opacity-50"
                            >
                                ✓ Save & Use
                            </button>
                            <button
                                on:click={cancelEditingProposal}
                                disabled={generating}
                                class="flex-1 inline-flex items-center justify-center gap-1 rounded-md bg-white dark:bg-gray-700 px-3 py-1.5 text-xs font-semibold text-gray-700 dark:text-gray-200 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                            >
                                ✕ Cancel
                            </button>
                        {:else}
                            <!-- Normal Mode Buttons -->
                            <button
                                on:click={() => useProposal(proposal)}
                                disabled={generating}
                                class="flex-1 inline-flex items-center justify-center gap-1 rounded-md bg-purple-600 dark:bg-purple-500 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-purple-500 dark:hover:bg-purple-400 disabled:opacity-50"
                            >
                                ✓ Use This
                            </button>
                            <button
                                on:click={() => startEditingProposal(i)}
                                disabled={generating}
                                class="flex-1 inline-flex items-center justify-center gap-1 rounded-md bg-white dark:bg-gray-700 px-3 py-1.5 text-xs font-semibold text-gray-700 dark:text-gray-200 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
                            >
                                ✎ Edit
                            </button>
                        {/if}
                    </div>
                </div>
            {/each}
        </div>

        <!-- Regenerate Button -->
        <button
            on:click={generateProposals}
            disabled={generating}
            class="w-full inline-flex items-center justify-center gap-2 rounded-md bg-white dark:bg-gray-700 px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-200 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50"
        >
            🔄 Regenerate Proposals
        </button>
    {:else if !generating}
        <div class="text-center py-8 text-gray-500 dark:text-gray-400">
            <p class="text-sm">No proposals yet. Click "Generate Proposals" to start.</p>
        </div>
    {/if}
</div>

<style>
    .proposal-card {
        cursor: pointer;
    }

    .proposal-card:hover {
        transform: translateY(-1px);
    }

    textarea {
        min-height: 80px;
    }

    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .animate-slideIn {
        animation: slideIn 0.3s ease-out;
    }
</style>
