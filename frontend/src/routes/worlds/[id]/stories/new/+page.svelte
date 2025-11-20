<script lang="ts">
    import { page } from "$app/stores";
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";
    import type { AuthoringMode, POVType } from "$lib/types";
    import { AUTHORING_MODE_LABELS, POV_TYPE_LABELS } from "$lib/types";

    let title = "";
    let synopsis = "";
    let theme = "";
    let mode: AuthoringMode = "manual";
    let pov_type: POVType = "third";
    let loading = false;
    let error = "";

    $: worldId = $page.params.id;

    async function handleSubmit() {
        loading = true;
        error = "";
        try {
            const story = await api.post<{ id: string }>(
                `/worlds/${worldId}/stories`,
                {
                    title,
                    synopsis,
                    theme,
                    status: "draft",
                    mode,
                    pov_type,
                },
            );
            goto(`/stories/${story.id}`);
        } catch (e: any) {
            error = e.message;
        } finally {
            loading = false;
        }
    }
</script>

<div class="max-w-2xl mx-auto">
    <div class="md:flex md:items-center md:justify-between mb-8">
        <div class="min-w-0 flex-1">
            <h2
                class="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight"
            >
                Create New Story
            </h2>
        </div>
    </div>

    <form
        on:submit|preventDefault={handleSubmit}
        class="space-y-6 bg-white shadow sm:rounded-lg p-6"
    >
        <div>
            <label
                for="title"
                class="block text-sm font-medium leading-6 text-gray-900"
                >Title</label
            >
            <div class="mt-2">
                <input
                    type="text"
                    name="title"
                    id="title"
                    required
                    class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    bind:value={title}
                />
            </div>
        </div>

        <div>
            <label
                for="synopsis"
                class="block text-sm font-medium leading-6 text-gray-900"
                >Synopsis</label
            >
            <div class="mt-2">
                <textarea
                    id="synopsis"
                    name="synopsis"
                    rows="3"
                    class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    bind:value={synopsis}
                ></textarea>
            </div>
        </div>

        <div>
            <label
                for="theme"
                class="block text-sm font-medium leading-6 text-gray-900"
                >Theme</label
            >
            <div class="mt-2">
                <input
                    type="text"
                    name="theme"
                    id="theme"
                    class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                    bind:value={theme}
                />
            </div>
        </div>

        <div>
            <label
                for="mode"
                class="block text-sm font-medium leading-6 text-gray-900"
                >Authoring Mode</label
            >
            <div class="mt-2">
                <select
                    id="mode"
                    name="mode"
                    bind:value={mode}
                    class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                >
                    {#each Object.entries(AUTHORING_MODE_LABELS) as [value, label]}
                        <option value={value}>{label}</option>
                    {/each}
                </select>
            </div>
            <p class="mt-1 text-sm text-gray-500">
                {#if mode === "autonomous"}
                    AI generates everything automatically
                {:else if mode === "collaborative"}
                    AI proposes content, you review and edit
                {:else}
                    You write manually, AI can assist
                {/if}
            </p>
        </div>

        <div>
            <label
                for="pov_type"
                class="block text-sm font-medium leading-6 text-gray-900"
                >Point of View</label
            >
            <div class="mt-2">
                <select
                    id="pov_type"
                    name="pov_type"
                    bind:value={pov_type}
                    class="block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"
                >
                    {#each Object.entries(POV_TYPE_LABELS) as [value, label]}
                        <option value={value}>{label}</option>
                    {/each}
                </select>
            </div>
        </div>

        {#if error}
            <div class="text-red-500 text-sm">{error}</div>
        {/if}

        <div class="flex justify-end gap-x-4">
            <a
                href="/worlds/{worldId}"
                class="rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
                >Cancel</a
            >
            <button
                type="submit"
                disabled={loading}
                class="rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50"
            >
                {#if loading}Creating...{:else}Create Story{/if}
            </button>
        </div>
    </form>
</div>
