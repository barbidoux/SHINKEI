<script lang="ts">
    import { createEventDispatcher } from 'svelte';
    import type { CoherenceSettings } from '$lib/types';
    import { api } from '$lib/api';
    import { addToast } from '$lib/stores/toast';

    export let worldId: string;
    export let settings: CoherenceSettings | null = null;

    const dispatch = createEventDispatcher<{
        updated: CoherenceSettings;
    }>();

    let loading = false;
    let saving = false;

    // Local form state
    let timeConsistency: CoherenceSettings['timeConsistency'] = 'strict';
    let spatialConsistency: CoherenceSettings['spatialConsistency'] = 'euclidean';
    let causality: CoherenceSettings['causality'] = 'strict';
    let characterKnowledge: CoherenceSettings['characterKnowledge'] = 'strict';
    let deathPermanence: CoherenceSettings['deathPermanence'] = 'permanent';
    let customRules: string[] = [];
    let newRule = '';

    // Sync from props
    $: if (settings) {
        timeConsistency = settings.timeConsistency;
        spatialConsistency = settings.spatialConsistency;
        causality = settings.causality;
        characterKnowledge = settings.characterKnowledge;
        deathPermanence = settings.deathPermanence;
        customRules = settings.customRules || [];
    }

    async function loadSettings() {
        loading = true;
        try {
            const response = await api.get<CoherenceSettings>(`/agent/worlds/${worldId}/coherence-settings`);
            settings = response;
        } catch (e: unknown) {
            const error = e as Error;
            console.error('Failed to load coherence settings:', error);
        } finally {
            loading = false;
        }
    }

    async function saveSettings() {
        saving = true;
        try {
            const response = await api.put<CoherenceSettings>(`/agent/worlds/${worldId}/coherence-settings`, {
                time_consistency: timeConsistency,
                spatial_consistency: spatialConsistency,
                causality,
                character_knowledge: characterKnowledge,
                death_permanence: deathPermanence,
                custom_rules: customRules.length > 0 ? customRules : null
            });
            settings = response;
            dispatch('updated', response);
            addToast({ type: 'success', message: 'Coherence settings saved' });
        } catch (e: unknown) {
            const error = e as Error;
            addToast({ type: 'error', message: error.message || 'Failed to save settings' });
        } finally {
            saving = false;
        }
    }

    function addCustomRule() {
        if (newRule.trim()) {
            customRules = [...customRules, newRule.trim()];
            newRule = '';
        }
    }

    function removeCustomRule(index: number) {
        customRules = customRules.filter((_, i) => i !== index);
    }

    // Load settings on mount if not provided
    $: if (worldId && !settings) {
        loadSettings();
    }

    const timeOptions = [
        { value: 'strict', label: 'Strict', description: 'Events follow linear timeline' },
        { value: 'flexible', label: 'Flexible', description: 'Minor time inconsistencies allowed' },
        { value: 'non-linear', label: 'Non-linear', description: 'Time travel and loops allowed' },
        { value: 'irrelevant', label: 'Irrelevant', description: 'Time is not tracked' }
    ];

    const spatialOptions = [
        { value: 'euclidean', label: 'Euclidean', description: 'Normal physics apply' },
        { value: 'flexible', label: 'Flexible', description: 'Some spatial liberties allowed' },
        { value: 'non-euclidean', label: 'Non-euclidean', description: 'Space can be warped/impossible' },
        { value: 'irrelevant', label: 'Irrelevant', description: 'Space is not tracked' }
    ];

    const causalityOptions = [
        { value: 'strict', label: 'Strict', description: 'Cause must precede effect' },
        { value: 'flexible', label: 'Flexible', description: 'Some causal loops allowed' },
        { value: 'paradox-allowed', label: 'Paradox Allowed', description: 'Paradoxes are valid' }
    ];

    const knowledgeOptions = [
        { value: 'strict', label: 'Strict', description: 'Characters only know what they\'ve learned' },
        { value: 'flexible', label: 'Flexible', description: 'Some information leakage allowed' }
    ];

    const deathOptions = [
        { value: 'permanent', label: 'Permanent', description: 'Death is final' },
        { value: 'reversible', label: 'Reversible', description: 'Resurrection is possible' },
        { value: 'fluid', label: 'Fluid', description: 'Death is a fluid concept' }
    ];
</script>

<div class="space-y-4">
    {#if loading}
        <div class="flex items-center justify-center py-8">
            <svg class="w-6 h-6 animate-spin text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        </div>
    {:else}
        <!-- Time Consistency -->
        <div>
            <label for="time-consistency" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Time Consistency
            </label>
            <select
                id="time-consistency"
                bind:value={timeConsistency}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
            >
                {#each timeOptions as opt}
                    <option value={opt.value}>{opt.label} - {opt.description}</option>
                {/each}
            </select>
        </div>

        <!-- Spatial Consistency -->
        <div>
            <label for="spatial-consistency" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Spatial Consistency
            </label>
            <select
                id="spatial-consistency"
                bind:value={spatialConsistency}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
            >
                {#each spatialOptions as opt}
                    <option value={opt.value}>{opt.label} - {opt.description}</option>
                {/each}
            </select>
        </div>

        <!-- Causality -->
        <div>
            <label for="causality" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Causality
            </label>
            <select
                id="causality"
                bind:value={causality}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
            >
                {#each causalityOptions as opt}
                    <option value={opt.value}>{opt.label} - {opt.description}</option>
                {/each}
            </select>
        </div>

        <!-- Character Knowledge -->
        <div>
            <label for="character-knowledge" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Character Knowledge
            </label>
            <select
                id="character-knowledge"
                bind:value={characterKnowledge}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
            >
                {#each knowledgeOptions as opt}
                    <option value={opt.value}>{opt.label} - {opt.description}</option>
                {/each}
            </select>
        </div>

        <!-- Death Permanence -->
        <div>
            <label for="death-permanence" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Death Permanence
            </label>
            <select
                id="death-permanence"
                bind:value={deathPermanence}
                class="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
            >
                {#each deathOptions as opt}
                    <option value={opt.value}>{opt.label} - {opt.description}</option>
                {/each}
            </select>
        </div>

        <!-- Custom Rules -->
        <div>
            <label for="new-custom-rule" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Custom Rules
            </label>
            <div class="flex gap-2 mb-2">
                <input
                    id="new-custom-rule"
                    type="text"
                    bind:value={newRule}
                    placeholder="Add a custom rule..."
                    class="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm"
                    on:keydown={(e) => e.key === 'Enter' && addCustomRule()}
                />
                <button
                    on:click={addCustomRule}
                    disabled={!newRule.trim()}
                    class="px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 text-sm"
                >
                    Add
                </button>
            </div>
            {#if customRules.length > 0}
                <ul class="space-y-1">
                    {#each customRules as rule, i}
                        <li class="flex items-center gap-2 px-2 py-1 bg-gray-50 dark:bg-gray-700 rounded text-sm">
                            <span class="flex-1">{rule}</span>
                            <button
                                on:click={() => removeCustomRule(i)}
                                class="text-gray-400 hover:text-red-500"
                                aria-label="Remove rule"
                            >
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </li>
                    {/each}
                </ul>
            {:else}
                <p class="text-xs text-gray-500 dark:text-gray-400">No custom rules defined</p>
            {/if}
        </div>

        <!-- Save Button -->
        <div class="pt-2">
            <button
                on:click={saveSettings}
                disabled={saving}
                class="w-full px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
                {#if saving}
                    <svg class="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                {/if}
                Save Coherence Settings
            </button>
        </div>
    {/if}
</div>
