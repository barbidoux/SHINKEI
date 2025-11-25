<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { AgentPersona } from '$lib/types';
    import { api } from '$lib/api';
    import { addToast } from '$lib/stores/toast';

    export let worldId: string;
    export let personas: AgentPersona[] = [];
    export let isOpen = false;

    const dispatch = createEventDispatcher<{
        close: void;
        personaCreated: AgentPersona;
        personaDeleted: string;
    }>();

    // Form state
    let isCreating = false;
    let showForm = false;
    let formData = {
        name: '',
        description: '',
        system_prompt: '',
        traits: {} as Record<string, string>,
        generation_defaults: {} as Record<string, unknown>
    };

    // Trait editing
    let newTraitKey = '';
    let newTraitValue = '';

    function resetForm() {
        formData = {
            name: '',
            description: '',
            system_prompt: '',
            traits: {},
            generation_defaults: {}
        };
        newTraitKey = '';
        newTraitValue = '';
        showForm = false;
    }

    async function handleCreate() {
        if (!formData.name || !formData.system_prompt) {
            addToast({ type: 'warning', message: 'Name and system prompt are required' });
            return;
        }

        isCreating = true;
        try {
            const response = await api.post<AgentPersona>(`/agent/worlds/${worldId}/personas`, formData);
            dispatch('personaCreated', response);
            addToast({ type: 'success', message: `Created persona "${response.name}"` });
            resetForm();
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to create persona' });
        } finally {
            isCreating = false;
        }
    }

    async function handleDelete(personaId: string, personaName: string) {
        if (!confirm(`Delete persona "${personaName}"? This cannot be undone.`)) {
            return;
        }

        try {
            await api.delete(`/agent/personas/${personaId}`);
            dispatch('personaDeleted', personaId);
            addToast({ type: 'success', message: `Deleted persona "${personaName}"` });
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to delete persona' });
        }
    }

    function addTrait() {
        if (newTraitKey && newTraitValue) {
            formData.traits[newTraitKey] = newTraitValue;
            formData = formData; // Trigger reactivity
            newTraitKey = '';
            newTraitValue = '';
        }
    }

    function removeTrait(key: string) {
        delete formData.traits[key];
        formData = formData; // Trigger reactivity
    }

    $: customPersonas = personas.filter(p => !p.isBuiltin);
    $: builtinPersonas = personas.filter(p => p.isBuiltin);
</script>

{#if isOpen}
    <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
    <div
        class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
        role="dialog"
        aria-modal="true"
        aria-labelledby="persona-manager-title"
        tabindex="-1"
        on:click={() => dispatch('close')}
        on:keydown={(e) => e.key === 'Escape' && dispatch('close')}
    >
        <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
        <div
            class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col"
            role="document"
            on:click|stopPropagation
            on:keydown|stopPropagation
        >
            <!-- Header -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between flex-shrink-0">
                <h2 id="persona-manager-title" class="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    Manage Personas
                </h2>
                <button
                    on:click={() => dispatch('close')}
                    class="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                    aria-label="Close"
                >
                    <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            <!-- Content -->
            <div class="flex-1 overflow-y-auto p-4 space-y-6">
                <!-- Create new persona button/form -->
                {#if !showForm}
                    <button
                        on:click={() => showForm = true}
                        class="w-full p-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 hover:border-indigo-400 hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors flex items-center justify-center gap-2"
                    >
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                        </svg>
                        Create New Persona
                    </button>
                {:else}
                    <!-- Creation form -->
                    <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-4">
                        <div class="flex items-center justify-between">
                            <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100">New Persona</h3>
                            <button
                                on:click={resetForm}
                                class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                            >
                                Cancel
                            </button>
                        </div>

                        <!-- Name -->
                        <div>
                            <label for="persona-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Name *
                            </label>
                            <input
                                id="persona-name"
                                type="text"
                                bind:value={formData.name}
                                placeholder="e.g., Drama Coach"
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                            />
                        </div>

                        <!-- Description -->
                        <div>
                            <label for="persona-description" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Description
                            </label>
                            <input
                                id="persona-description"
                                type="text"
                                bind:value={formData.description}
                                placeholder="Brief description of this persona"
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                            />
                        </div>

                        <!-- System Prompt -->
                        <div>
                            <label for="persona-prompt" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                System Prompt *
                            </label>
                            <textarea
                                id="persona-prompt"
                                bind:value={formData.system_prompt}
                                rows="4"
                                placeholder="Instructions that define how this persona behaves..."
                                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm resize-none"
                            ></textarea>
                            <p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
                                This prompt is prepended to every conversation with this persona.
                            </p>
                        </div>

                        <!-- Traits -->
                        <div>
                            <span class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                Personality Traits
                            </span>
                            <div class="flex gap-2 mb-2">
                                <input
                                    type="text"
                                    bind:value={newTraitKey}
                                    placeholder="Trait name"
                                    aria-label="Trait name"
                                    class="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                                />
                                <input
                                    type="text"
                                    bind:value={newTraitValue}
                                    placeholder="Value"
                                    aria-label="Trait value"
                                    class="flex-1 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                                />
                                <button
                                    on:click={addTrait}
                                    disabled={!newTraitKey || !newTraitValue}
                                    class="px-2 py-1 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50"
                                >
                                    Add
                                </button>
                            </div>
                            {#if Object.keys(formData.traits).length > 0}
                                <div class="flex flex-wrap gap-1">
                                    {#each Object.entries(formData.traits) as [key, value]}
                                        <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs">
                                            <span class="font-medium">{key}:</span> {value}
                                            <button
                                                on:click={() => removeTrait(key)}
                                                class="text-gray-400 hover:text-red-500"
                                                aria-label="Remove trait {key}"
                                            >
                                                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                                </svg>
                                            </button>
                                        </span>
                                    {/each}
                                </div>
                            {/if}
                        </div>

                        <!-- Submit -->
                        <div class="flex justify-end gap-2 pt-2">
                            <button
                                on:click={resetForm}
                                class="px-3 py-1.5 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                            >
                                Cancel
                            </button>
                            <button
                                on:click={handleCreate}
                                disabled={isCreating || !formData.name || !formData.system_prompt}
                                class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:opacity-50 flex items-center gap-1"
                            >
                                {#if isCreating}
                                    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                {/if}
                                Create Persona
                            </button>
                        </div>
                    </div>
                {/if}

                <!-- Custom Personas -->
                {#if customPersonas.length > 0}
                    <div>
                        <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                            Your Personas ({customPersonas.length})
                        </h3>
                        <div class="space-y-2">
                            {#each customPersonas as persona}
                                <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                                    <div class="flex items-start justify-between">
                                        <div class="flex-1 min-w-0">
                                            <h4 class="font-medium text-gray-900 dark:text-gray-100">{persona.name}</h4>
                                            {#if persona.description}
                                                <p class="text-sm text-gray-500 dark:text-gray-400 truncate">{persona.description}</p>
                                            {/if}
                                        </div>
                                        <button
                                            on:click={() => handleDelete(persona.id, persona.name)}
                                            class="p-1 text-gray-400 hover:text-red-500"
                                            title="Delete persona"
                                        >
                                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    </div>
                                    {#if persona.traits && Object.keys(persona.traits).length > 0}
                                        <div class="mt-2 flex flex-wrap gap-1">
                                            {#each Object.entries(persona.traits) as [key, value]}
                                                <span class="px-1.5 py-0.5 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-600 dark:text-gray-400">
                                                    {key}: {value}
                                                </span>
                                            {/each}
                                        </div>
                                    {/if}
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}

                <!-- Builtin Personas -->
                {#if builtinPersonas.length > 0}
                    <div>
                        <h3 class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-2">
                            Built-in Personas ({builtinPersonas.length})
                        </h3>
                        <div class="space-y-2">
                            {#each builtinPersonas as persona}
                                <div class="border border-gray-200 dark:border-gray-700 rounded-lg p-3 bg-gray-50 dark:bg-gray-800/50">
                                    <div class="flex items-start gap-2">
                                        <div class="flex-1 min-w-0">
                                            <div class="flex items-center gap-2">
                                                <h4 class="font-medium text-gray-900 dark:text-gray-100">{persona.name}</h4>
                                                <span class="text-[10px] px-1 py-0.5 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded">Built-in</span>
                                            </div>
                                            {#if persona.description}
                                                <p class="text-sm text-gray-500 dark:text-gray-400">{persona.description}</p>
                                            {/if}
                                        </div>
                                    </div>
                                </div>
                            {/each}
                        </div>
                    </div>
                {/if}
            </div>
        </div>
    </div>
{/if}
