<script lang="ts">
    import { page } from "$app/stores";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import { api } from "$lib/api";
    import type { Story, AuthoringMode, POVType } from "$lib/types";
    import { AUTHORING_MODE_LABELS, POV_TYPE_LABELS } from "$lib/types";
    import TagInput from "$lib/components/TagInput.svelte";

    let title = "";
    let synopsis = "";
    let theme = "";
    let status: "draft" | "active" | "completed" | "archived" = "draft";
    let mode: AuthoringMode = "manual";
    let pov_type: POVType = "third";
    let tags: string[] = [];
    let loading = false;
    let loadingStory = true;
    let error = "";
    let worldId = "";

    $: storyId = $page.params.id;

    const statusOptions = [
        { value: "draft", label: "Draft", description: "Work in progress" },
        { value: "active", label: "Active", description: "Currently being written" },
        { value: "completed", label: "Completed", description: "Finished story" },
        { value: "archived", label: "Archived", description: "Archived for later" },
    ];

    onMount(async () => {
        try {
            const story = await api.get<Story>(`/stories/${storyId}`);
            title = story.title;
            synopsis = story.synopsis || "";
            theme = story.theme || "";
            status = story.status as "draft" | "active" | "completed" | "archived";
            mode = story.mode;
            pov_type = story.pov_type;
            tags = story.tags || [];
            worldId = story.world_id;
            loadingStory = false;
        } catch (e: any) {
            error = e.message || "Failed to load story";
            loadingStory = false;
        }
    });

    async function handleSubmit() {
        loading = true;
        error = "";

        try {
            const storyData = {
                title,
                synopsis: synopsis || undefined,
                theme: theme || undefined,
                status,
                mode,
                pov_type,
                tags,
            };

            await api.put(`/stories/${storyId}`, storyData);
            goto(`/stories/${storyId}`);
        } catch (e: any) {
            error = e.message || "Failed to update story";
        } finally {
            loading = false;
        }
    }

    function handleCancel() {
        goto(`/stories/${storyId}`);
    }
</script>

{#if loadingStory}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-gray-500 dark:text-gray-400">Loading story...</p>
        </div>
    </div>
{:else if error && !title}
    <div class="flex items-center justify-center min-h-screen">
        <div class="text-center">
            <p class="text-red-500 dark:text-red-400">{error}</p>
            <button
                on:click={() => goto("/worlds")}
                class="mt-4 text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
                ← Back to Worlds
            </button>
        </div>
    </div>
{:else}
    <div class="max-w-3xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        <div class="mb-6">
            <h1 class="text-3xl font-bold text-gray-900 dark:text-gray-100">Edit Story</h1>
            <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">
                Update your story's metadata and settings
            </p>
        </div>

        <form on:submit|preventDefault={handleSubmit} class="space-y-6 bg-white dark:bg-gray-800 shadow sm:rounded-lg p-6">
            <!-- Title -->
            <div>
                <label
                    for="title"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Title <span class="text-red-500">*</span>
                </label>
                <input
                    type="text"
                    id="title"
                    bind:value={title}
                    required
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                    placeholder="My Story Title"
                />
            </div>

            <!-- Synopsis -->
            <div>
                <label
                    for="synopsis"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Synopsis (optional)
                </label>
                <textarea
                    id="synopsis"
                    bind:value={synopsis}
                    rows="4"
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                    placeholder="A brief summary of your story..."
                ></textarea>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    A brief overview of the story's plot and themes
                </p>
            </div>

            <!-- Theme -->
            <div>
                <label
                    for="theme"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Theme (optional)
                </label>
                <input
                    type="text"
                    id="theme"
                    bind:value={theme}
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                    placeholder="e.g., redemption, loss, coming of age"
                />
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    The central theme or message of the story
                </p>
            </div>

            <!-- Tags -->
            <div>
                <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Tags (optional)
                </label>
                <TagInput bind:tags {worldId} />
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    Add tags to organize and categorize your story
                </p>
            </div>

            <!-- Status -->
            <div>
                <label
                    for="status"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Status
                </label>
                <select
                    id="status"
                    bind:value={status}
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                >
                    {#each statusOptions as option}
                        <option value={option.value}>{option.label}</option>
                    {/each}
                </select>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {#if status === "draft"}
                        Work in progress, not yet finalized
                    {:else if status === "active"}
                        Currently being actively written
                    {:else if status === "completed"}
                        This story is finished
                    {:else if status === "archived"}
                        Archived for later reference
                    {/if}
                </p>
            </div>

            <!-- Authoring Mode -->
            <div>
                <label
                    for="mode"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Authoring Mode
                </label>
                <select
                    id="mode"
                    bind:value={mode}
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                >
                    {#each Object.entries(AUTHORING_MODE_LABELS) as [value, label]}
                        <option value={value}>{label}</option>
                    {/each}
                </select>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {#if mode === "autonomous"}
                        AI writes everything automatically
                    {:else if mode === "collaborative"}
                        AI proposes content, you review and edit
                    {:else}
                        You write manually, AI can assist with coherence
                    {/if}
                </p>
            </div>

            <!-- Point of View -->
            <div>
                <label
                    for="pov_type"
                    class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
                >
                    Point of View
                </label>
                <select
                    id="pov_type"
                    bind:value={pov_type}
                    class="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-indigo-500 dark:focus:border-indigo-400 focus:ring-indigo-500 dark:focus:ring-indigo-400 sm:text-sm"
                >
                    {#each Object.entries(POV_TYPE_LABELS) as [value, label]}
                        <option value={value}>{label}</option>
                    {/each}
                </select>
                <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    {#if pov_type === "first"}
                        First person narrative (I, we)
                    {:else if pov_type === "third"}
                        Third person narrative (he, she, they)
                    {:else}
                        Third person omniscient narrator
                    {/if}
                </p>
            </div>

            <!-- Error Message -->
            {#if error}
                <div class="rounded-md bg-red-50 dark:bg-red-900/30 p-4 border border-red-200 dark:border-red-700">
                    <p class="text-sm text-red-800 dark:text-red-300">{error}</p>
                </div>
            {/if}

            <!-- Action Buttons -->
            <div class="flex items-center justify-end gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
                <button
                    type="button"
                    on:click={handleCancel}
                    disabled={loading}
                    class="rounded-md bg-white dark:bg-gray-700 px-4 py-2 text-sm font-semibold text-gray-700 dark:text-gray-200 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    disabled={loading}
                    class="rounded-md bg-indigo-600 dark:bg-indigo-500 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 dark:hover:bg-indigo-400 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 dark:focus-visible:outline-indigo-400 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {#if loading}
                        <span class="flex items-center gap-2">
                            <svg class="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Saving...
                        </span>
                    {:else}
                        Save Changes
                    {/if}
                </button>
            </div>
        </form>
    </div>
{/if}
