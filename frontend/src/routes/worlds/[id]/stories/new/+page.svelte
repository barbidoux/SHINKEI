<script lang="ts">
    import { page } from "$app/stores";
    import { api } from "$lib/api";
    import { goto } from "$app/navigation";
    import { onMount } from "svelte";
    import type { AuthoringMode, POVType, StoryTemplate } from "$lib/types";
    import { AUTHORING_MODE_LABELS, POV_TYPE_LABELS } from "$lib/types";
    import TagInput from "$lib/components/TagInput.svelte";
    import { AIGenerationOptions } from "$lib/components";
    import type { GeneratedTemplate, AIProvider } from "$lib/types/entity-generation";

    let title = "";
    let synopsis = "";
    let theme = "";
    let mode: AuthoringMode = "manual";
    let pov_type: POVType = "third";
    let tags: string[] = [];
    let loading = false;
    let loadingTemplates = true;
    let error = "";
    let selectedTemplate: string = "";
    let templates: Record<string, StoryTemplate> = {};

    // AI Template Generation state
    let showAIInputModal = false;
    let showAIResultModal = false;
    let aiGenerating = false;
    let aiError = "";
    let aiGeneratedTemplate: GeneratedTemplate | null = null;

    // AI Generation parameters
    let aiUserPrompt = "";
    let aiPreferredMode: "autonomous" | "collaborative" | "manual" | "" = "";
    let aiPreferredPov: "first" | "third" | "omniscient" | "" = "";
    let aiTargetLength: "short" | "medium" | "long" | "" = "";
    let aiProvider: AIProvider | null = null;
    let aiModel = "";
    let aiTemperature: number | null = null;
    let aiOptionsExpanded = false;

    $: worldId = $page.params.id;

    onMount(async () => {
        try {
            const response = await api.get<{ templates: Record<string, StoryTemplate> }>('/stories/templates');
            templates = response.templates;
            loadingTemplates = false;
        } catch (e) {
            console.error('Failed to load templates:', e);
            loadingTemplates = false;
        }
    });

    function applyTemplate(templateId: string) {
        if (!templateId || templateId === "") {
            return;
        }

        const template = templates[templateId];
        if (template) {
            synopsis = template.synopsis || "";
            theme = template.theme || "";
            mode = template.mode;
            pov_type = template.pov_type;
            tags = template.suggested_tags || [];
        }
    }

    $: if (selectedTemplate) {
        applyTemplate(selectedTemplate);
    }

    // AI Template Generation Functions
    function openAIGenerationModal() {
        aiUserPrompt = "";
        aiPreferredMode = "";
        aiPreferredPov = "";
        aiTargetLength = "";
        aiProvider = null;
        aiModel = "";
        aiTemperature = null;
        aiOptionsExpanded = false;
        aiError = "";
        aiGeneratedTemplate = null;
        showAIInputModal = true;
    }

    async function generateAITemplate() {
        aiGenerating = true;
        aiError = "";

        try {
            const requestBody: Record<string, any> = {};
            if (aiUserPrompt) requestBody.user_prompt = aiUserPrompt;
            if (aiPreferredMode) requestBody.preferred_mode = aiPreferredMode;
            if (aiPreferredPov) requestBody.preferred_pov = aiPreferredPov;
            if (aiTargetLength) requestBody.target_length = aiTargetLength;
            if (aiProvider) requestBody.provider = aiProvider;
            if (aiModel) requestBody.model = aiModel;
            if (aiTemperature !== null) requestBody.temperature = aiTemperature;

            const response = await api.post<GeneratedTemplate>(
                `/worlds/${worldId}/templates/generate`,
                requestBody
            );

            aiGeneratedTemplate = response;
            showAIInputModal = false;
            showAIResultModal = true;
        } catch (e: any) {
            aiError = e.message || "Failed to generate template";
        } finally {
            aiGenerating = false;
        }
    }

    function applyAITemplate() {
        if (aiGeneratedTemplate) {
            synopsis = aiGeneratedTemplate.synopsis;
            theme = aiGeneratedTemplate.theme;
            mode = aiGeneratedTemplate.mode as AuthoringMode;
            pov_type = aiGeneratedTemplate.pov_type as POVType;
            tags = aiGeneratedTemplate.suggested_tags;
            showAIResultModal = false;
        }
    }

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
                    tags,
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
        <!-- Template Selector -->
        <div>
            <label
                for="template"
                class="block text-sm font-medium leading-6 text-gray-900"
                >Story Template (optional)</label
            >
            <div class="mt-2 flex gap-3">
                <select
                    id="template"
                    name="template"
                    bind:value={selectedTemplate}
                    disabled={loadingTemplates}
                    class="block flex-1 rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 disabled:opacity-50"
                >
                    <option value="">Start from scratch</option>
                    {#each Object.entries(templates) as [id, template]}
                        <option value={id}>{template.name}</option>
                    {/each}
                </select>
                <button
                    type="button"
                    on:click={openAIGenerationModal}
                    class="inline-flex items-center rounded-md bg-purple-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-purple-500"
                >
                    <svg class="w-4 h-4 mr-1.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    AI Generate
                </button>
            </div>
            {#if selectedTemplate && templates[selectedTemplate]}
                <p class="mt-1 text-sm text-gray-500">
                    {templates[selectedTemplate].description}
                </p>
            {/if}
        </div>

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

        <!-- Tags -->
        <div>
            <label class="block text-sm font-medium leading-6 text-gray-900">
                Tags (optional)
            </label>
            <div class="mt-2">
                <TagInput bind:tags {worldId} />
            </div>
            <p class="mt-1 text-sm text-gray-500">
                Add tags to organize and categorize your story
            </p>
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

<!-- AI Template Generation Input Modal -->
{#if showAIInputModal}
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40"></div>
    <div class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
            <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
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
                        <h3 class="text-lg font-semibold leading-6 text-gray-900">Generate Story Template with AI</h3>
                        <p class="mt-1 text-sm text-gray-500">
                            Describe the type of story you want and AI will generate a custom template.
                        </p>
                    </div>
                </div>

                <form on:submit|preventDefault={generateAITemplate} class="mt-6 space-y-4">
                    <!-- Story Description -->
                    <div>
                        <label for="ai-prompt" class="block text-sm font-medium text-gray-700">
                            Describe Your Story
                        </label>
                        <textarea
                            id="ai-prompt"
                            bind:value={aiUserPrompt}
                            rows="3"
                            placeholder="e.g., A noir detective story in a cyberpunk city..."
                            class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                        ></textarea>
                    </div>

                    <!-- Preferences Grid -->
                    <div class="grid grid-cols-3 gap-4">
                        <div>
                            <label for="ai-mode" class="block text-sm font-medium text-gray-700">Mode</label>
                            <select
                                id="ai-mode"
                                bind:value={aiPreferredMode}
                                class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            >
                                <option value="">Any</option>
                                <option value="autonomous">Autonomous</option>
                                <option value="collaborative">Collaborative</option>
                                <option value="manual">Manual</option>
                            </select>
                        </div>
                        <div>
                            <label for="ai-pov" class="block text-sm font-medium text-gray-700">POV</label>
                            <select
                                id="ai-pov"
                                bind:value={aiPreferredPov}
                                class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            >
                                <option value="">Any</option>
                                <option value="first">First Person</option>
                                <option value="third">Third Person</option>
                                <option value="omniscient">Omniscient</option>
                            </select>
                        </div>
                        <div>
                            <label for="ai-length" class="block text-sm font-medium text-gray-700">Length</label>
                            <select
                                id="ai-length"
                                bind:value={aiTargetLength}
                                class="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            >
                                <option value="">Any</option>
                                <option value="short">Short</option>
                                <option value="medium">Medium</option>
                                <option value="long">Long</option>
                            </select>
                        </div>
                    </div>

                    <!-- AI Options -->
                    <AIGenerationOptions
                        bind:provider={aiProvider}
                        bind:model={aiModel}
                        bind:temperature={aiTemperature}
                        bind:expanded={aiOptionsExpanded}
                    />

                    {#if aiError}
                        <div class="rounded-md bg-red-50 p-4">
                            <p class="text-sm text-red-700">{aiError}</p>
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
                                Generate Template
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

<!-- AI Generated Template Result Modal -->
{#if showAIResultModal && aiGeneratedTemplate}
    <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity z-40"></div>
    <div class="fixed inset-0 z-50 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
            <div class="relative transform overflow-hidden rounded-lg bg-white px-4 pb-4 pt-5 text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg sm:p-6">
                <div class="absolute right-0 top-0 pr-4 pt-4">
                    <button
                        type="button"
                        class="rounded-md text-gray-400 hover:text-gray-500"
                        on:click={() => (showAIResultModal = false)}
                    >
                        <span class="sr-only">Close</span>
                        <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div class="sm:flex sm:items-start mb-4">
                    <div class="mx-auto flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-full bg-green-100 sm:mx-0 sm:h-10 sm:w-10">
                        <svg class="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <div class="mt-3 text-center sm:ml-4 sm:mt-0 sm:text-left">
                        <h3 class="text-lg font-semibold leading-6 text-gray-900">AI Generated Template</h3>
                        <p class="mt-1 text-sm text-gray-500">
                            Review the template below and apply it to your story.
                        </p>
                    </div>
                </div>

                <div class="border border-gray-200 rounded-lg p-4 space-y-3">
                    <div>
                        <span class="text-xs font-medium text-gray-500 uppercase">Template Name</span>
                        <p class="text-sm font-semibold text-gray-900">{aiGeneratedTemplate.name}</p>
                    </div>

                    <div>
                        <span class="text-xs font-medium text-gray-500 uppercase">Description</span>
                        <p class="text-sm text-gray-700">{aiGeneratedTemplate.description}</p>
                    </div>

                    <div>
                        <span class="text-xs font-medium text-gray-500 uppercase">Synopsis</span>
                        <p class="text-sm text-gray-700">{aiGeneratedTemplate.synopsis}</p>
                    </div>

                    <div>
                        <span class="text-xs font-medium text-gray-500 uppercase">Theme</span>
                        <p class="text-sm text-gray-700">{aiGeneratedTemplate.theme}</p>
                    </div>

                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <span class="text-xs font-medium text-gray-500 uppercase">Mode</span>
                            <p class="text-sm text-gray-700 capitalize">{aiGeneratedTemplate.mode}</p>
                        </div>
                        <div>
                            <span class="text-xs font-medium text-gray-500 uppercase">POV</span>
                            <p class="text-sm text-gray-700 capitalize">{aiGeneratedTemplate.pov_type}</p>
                        </div>
                    </div>

                    {#if aiGeneratedTemplate.suggested_tags.length > 0}
                        <div>
                            <span class="text-xs font-medium text-gray-500 uppercase">Suggested Tags</span>
                            <div class="mt-1 flex flex-wrap gap-1">
                                {#each aiGeneratedTemplate.suggested_tags as tag}
                                    <span class="inline-flex items-center rounded-full bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700">
                                        {tag}
                                    </span>
                                {/each}
                            </div>
                        </div>
                    {/if}

                    {#if aiGeneratedTemplate.reasoning}
                        <details class="mt-2">
                            <summary class="text-xs text-gray-400 cursor-pointer hover:text-gray-500">
                                AI reasoning
                            </summary>
                            <p class="mt-1 text-xs text-gray-500 italic">
                                {aiGeneratedTemplate.reasoning}
                            </p>
                        </details>
                    {/if}
                </div>

                <div class="mt-5 sm:mt-4 sm:flex sm:flex-row-reverse gap-3">
                    <button
                        type="button"
                        on:click={applyAITemplate}
                        class="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 sm:w-auto"
                    >
                        Apply Template
                    </button>
                    <button
                        type="button"
                        class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                        on:click={() => {
                            showAIResultModal = false;
                            openAIGenerationModal();
                        }}
                    >
                        Generate Another
                    </button>
                    <button
                        type="button"
                        class="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-500 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
                        on:click={() => (showAIResultModal = false)}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    </div>
{/if}
