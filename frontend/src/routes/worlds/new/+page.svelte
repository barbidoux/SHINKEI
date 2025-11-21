<script lang="ts">
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import type { ChronologyMode, WorldLaws } from "$lib/types";

    interface WorldTemplate {
        name: string;
        description: string;
        tone: string;
        chronology_mode: string;
    }

    interface TemplateDetails {
        name: string;
        description: string;
        tone: string;
        backdrop: string;
        laws_physics: string;
        laws_metaphysics: string;
        laws_social: string;
        laws_forbidden: string;
        chronology_mode: string;
    }

    let name = "";
    let description = "";
    let tone = "";
    let backdrop = "";
    let chronology_mode: ChronologyMode = "linear";
    let physics = "";
    let metaphysics = "";
    let social = "";
    let forbidden = "";
    let loading = false;
    let loadingTemplates = true;
    let error = "";
    let templates: Record<string, WorldTemplate> = {};
    let selectedTemplateId: string | null = null;
    let showAdvanced = false;

    const chronologyModes: {
        value: ChronologyMode;
        label: string;
        description: string;
    }[] = [
        {
            value: "linear",
            label: "Linear",
            description: "Events follow a strict chronological order",
        },
        {
            value: "fragmented",
            label: "Fragmented",
            description: "Non-linear narrative with flashbacks and time jumps",
        },
        {
            value: "timeless",
            label: "Timeless",
            description: "No fixed timeline, events float in time",
        },
    ];

    onMount(async () => {
        try {
            const response = await api.get<{ templates: Record<string, WorldTemplate> }>("/worlds/templates");
            templates = response.templates;
            loadingTemplates = false;
        } catch (e: any) {
            error = "Failed to load templates";
            loadingTemplates = false;
        }
    });

    async function selectTemplate(templateId: string) {
        selectedTemplateId = templateId;
        const template = templates[templateId];

        if (!template) return;

        // Populate form with template values
        name = template.name;
        description = template.description;
        tone = template.tone;
        chronology_mode = template.chronology_mode as ChronologyMode;

        // For detailed template data, we'll let the backend handle it
        // User can customize these values before submitting
        showAdvanced = templateId !== "blank";
    }

    function clearTemplate() {
        selectedTemplateId = null;
        name = "";
        description = "";
        tone = "";
        backdrop = "";
        chronology_mode = "linear";
        physics = "";
        metaphysics = "";
        social = "";
        forbidden = "";
        showAdvanced = false;
    }

    async function handleSubmit() {
        loading = true;
        error = "";
        try {
            const laws: WorldLaws = {};
            if (physics) laws.physics = physics;
            if (metaphysics) laws.metaphysics = metaphysics;
            if (social) laws.social = social;
            if (forbidden) laws.forbidden = forbidden;

            const worldData = {
                name,
                description: description || undefined,
                tone: tone || undefined,
                backdrop: backdrop || undefined,
                laws,
                chronology_mode,
            };

            // Add template_id as query parameter if selected
            const url = selectedTemplateId
                ? `/worlds?template_id=${selectedTemplateId}`
                : "/worlds";

            const world = await api.post<{ id: string }>(url, worldData);
            goto(`/worlds/${world.id}`);
        } catch (e: any) {
            error = e.message || "Failed to create world";
        } finally {
            loading = false;
        }
    }
</script>

<div class="max-w-3xl mx-auto py-8">
    <div class="mb-6">
        <h1 class="text-3xl font-bold text-gray-900">Create New World</h1>
        <p class="mt-2 text-sm text-gray-500">
            Choose a template or start from scratch to build your narrative world
        </p>
    </div>

    <!-- Template Selector -->
    {#if !loadingTemplates}
        <div class="mb-8 bg-white shadow sm:rounded-lg p-6">
            <h2 class="text-lg font-medium text-gray-900 mb-4">Choose a Template</h2>
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {#each Object.entries(templates) as [templateId, template]}
                    <button
                        type="button"
                        on:click={() => selectTemplate(templateId)}
                        class="relative rounded-lg border {selectedTemplateId === templateId
                            ? 'border-indigo-500 ring-2 ring-indigo-500'
                            : 'border-gray-300 hover:border-indigo-300'} bg-white px-4 py-3 text-left transition-all"
                    >
                        <div class="font-medium text-gray-900">{template.name}</div>
                        <div class="mt-1 text-sm text-gray-500 line-clamp-2">
                            {template.description}
                        </div>
                        {#if selectedTemplateId === templateId}
                            <div
                                class="absolute top-2 right-2 h-5 w-5 rounded-full bg-indigo-500 flex items-center justify-center"
                            >
                                <svg
                                    class="h-3 w-3 text-white"
                                    fill="currentColor"
                                    viewBox="0 0 12 12"
                                >
                                    <path
                                        d="M3.707 5.293a1 1 0 00-1.414 1.414l1.414-1.414zM5 8l-.707.707a1 1 0 001.414 0L5 8zm4.707-3.293a1 1 0 00-1.414-1.414l1.414 1.414zm-7.414 2l2 2 1.414-1.414-2-2-1.414 1.414zm3.414 2l4-4-1.414-1.414-4 4 1.414 1.414z"
                                    />
                                </svg>
                            </div>
                        {/if}
                    </button>
                {/each}
            </div>
            {#if selectedTemplateId}
                <button
                    type="button"
                    on:click={clearTemplate}
                    class="mt-4 text-sm text-indigo-600 hover:text-indigo-500"
                >
                    Clear template selection
                </button>
            {/if}
        </div>
    {/if}

    <!-- World Creation Form -->
    <form on:submit|preventDefault={handleSubmit} class="space-y-6 bg-white shadow sm:rounded-lg p-6">
        <!-- Name -->
        <div>
            <label for="name" class="block text-sm font-medium text-gray-700 mb-2">
                World Name <span class="text-red-500">*</span>
            </label>
            <input
                type="text"
                id="name"
                bind:value={name}
                required
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="My Narrative World"
            />
        </div>

        <!-- Description -->
        <div>
            <label for="description" class="block text-sm font-medium text-gray-700 mb-2">
                Overview (optional)
            </label>
            <textarea
                id="description"
                bind:value={description}
                rows="3"
                class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                placeholder="A brief overview of this world..."
            ></textarea>
        </div>

        <!-- Advanced Fields Toggle -->
        <div>
            <button
                type="button"
                on:click={() => (showAdvanced = !showAdvanced)}
                class="text-sm font-medium text-indigo-600 hover:text-indigo-500"
            >
                {showAdvanced ? "Hide" : "Show"} advanced options
            </button>
        </div>

        {#if showAdvanced}
            <!-- Tone -->
            <div>
                <label for="tone" class="block text-sm font-medium text-gray-700 mb-2">
                    Tone (optional)
                </label>
                <input
                    type="text"
                    id="tone"
                    bind:value={tone}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="e.g., dark, whimsical, gritty, hopeful"
                />
                <p class="mt-1 text-xs text-gray-500">
                    The emotional atmosphere and feel of this world
                </p>
            </div>

            <!-- Backdrop -->
            <div>
                <label for="backdrop" class="block text-sm font-medium text-gray-700 mb-2">
                    Backdrop (optional)
                </label>
                <textarea
                    id="backdrop"
                    bind:value={backdrop}
                    rows="3"
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    placeholder="The historical, cultural, or environmental context..."
                ></textarea>
                <p class="mt-1 text-xs text-gray-500">
                    The setting and context in which stories unfold
                </p>
            </div>

            <!-- Chronology Mode -->
            <div>
                <label for="chronology_mode" class="block text-sm font-medium text-gray-700 mb-2">
                    Chronology Mode
                </label>
                <select
                    id="chronology_mode"
                    bind:value={chronology_mode}
                    class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                    {#each chronologyModes as mode}
                        <option value={mode.value}>{mode.label}</option>
                    {/each}
                </select>
                {#each chronologyModes as mode}
                    {#if chronology_mode === mode.value}
                        <p class="mt-1 text-sm text-gray-500">
                            {mode.description}
                        </p>
                    {/if}
                {/each}
            </div>

            <!-- World Laws Section -->
            <div class="border-t border-gray-200 pt-6">
                <h3 class="text-lg font-medium text-gray-900 mb-4">World Laws (Optional)</h3>
                <p class="text-sm text-gray-500 mb-4">
                    Define the rules and constraints that govern this world
                </p>

                <div class="space-y-4">
                    <!-- Physics -->
                    <div>
                        <label for="physics" class="block text-sm font-medium text-gray-700 mb-2">
                            Physical Laws
                        </label>
                        <textarea
                            id="physics"
                            bind:value={physics}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="How does the physical world work? Gravity, magic, technology..."
                        ></textarea>
                    </div>

                    <!-- Metaphysics -->
                    <div>
                        <label for="metaphysics" class="block text-sm font-medium text-gray-700 mb-2">
                            Metaphysical Laws
                        </label>
                        <textarea
                            id="metaphysics"
                            bind:value={metaphysics}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="Souls, afterlife, consciousness, reality..."
                        ></textarea>
                    </div>

                    <!-- Social -->
                    <div>
                        <label for="social" class="block text-sm font-medium text-gray-700 mb-2">
                            Social Laws
                        </label>
                        <textarea
                            id="social"
                            bind:value={social}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="Cultural norms, taboos, hierarchies, customs..."
                        ></textarea>
                    </div>

                    <!-- Forbidden -->
                    <div>
                        <label for="forbidden" class="block text-sm font-medium text-gray-700 mb-2">
                            Forbidden Elements
                        </label>
                        <textarea
                            id="forbidden"
                            bind:value={forbidden}
                            rows="2"
                            class="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                            placeholder="What should never appear in this world?"
                        ></textarea>
                    </div>
                </div>
            </div>
        {/if}

        <!-- Error Display -->
        {#if error}
            <div class="rounded-md bg-red-50 p-4 border border-red-200">
                <p class="text-sm text-red-800">{error}</p>
            </div>
        {/if}

        <!-- Actions -->
        <div class="flex items-center justify-between pt-4">
            <button
                type="button"
                on:click={() => goto("/worlds")}
                class="rounded-md bg-white px-4 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50"
            >
                Cancel
            </button>
            <button
                type="submit"
                disabled={loading || !name.trim()}
                class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
                {#if loading}
                    Creating...
                {:else}
                    Create World
                {/if}
            </button>
        </div>
    </form>
</div>
