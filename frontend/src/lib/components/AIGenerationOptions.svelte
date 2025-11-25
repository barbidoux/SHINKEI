<script lang="ts">
	import { AI_PROVIDERS, PROVIDER_MODELS, PROVIDER_TEMPERATURE_RANGES, type AIProvider } from '$lib/types/entity-generation';

	// Bindable state
	export let provider: AIProvider | null = null;
	export let model: string = '';
	export let temperature: number | null = null;
	export let expanded: boolean = false;

	// Computed values
	$: currentProvider = provider ?? 'openai';
	$: modelSuggestions = PROVIDER_MODELS[currentProvider] ?? [];
	$: tempRange = PROVIDER_TEMPERATURE_RANGES[currentProvider] ?? { min: 0, max: 1, default: 0.7 };
	$: displayTemperature = temperature ?? tempRange.default;

	function handleProviderChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		const newProvider = target.value === '' ? null : (target.value as AIProvider);
		provider = newProvider;

		// Reset model when provider changes
		model = '';

		// Reset temperature to new provider's default
		if (newProvider) {
			const newRange = PROVIDER_TEMPERATURE_RANGES[newProvider];
			temperature = newRange.default;
		} else {
			temperature = null;
		}
	}

	function handleTemperatureChange(e: Event) {
		const target = e.target as HTMLInputElement;
		temperature = parseFloat(target.value);
	}

	function toggleExpanded() {
		expanded = !expanded;
	}
</script>

<div class="ai-generation-options">
	<!-- Collapsible Header -->
	<button
		type="button"
		class="w-full flex items-center justify-between py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
		on:click={toggleExpanded}
	>
		<span class="flex items-center gap-2">
			<svg
				class="w-4 h-4 transition-transform {expanded ? 'rotate-90' : ''}"
				fill="none"
				stroke="currentColor"
				viewBox="0 0 24 24"
			>
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
			</svg>
			Advanced AI Options
		</span>
		{#if provider || model || temperature !== null}
			<span class="text-xs text-indigo-600 dark:text-indigo-400">
				(Custom settings)
			</span>
		{/if}
	</button>

	<!-- Collapsible Content -->
	{#if expanded}
		<div class="mt-3 space-y-4 p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
			<!-- Provider Selection -->
			<div>
				<label for="ai-provider" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					AI Provider
				</label>
				<select
					id="ai-provider"
					value={provider ?? ''}
					on:change={handleProviderChange}
					class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
				>
					<option value="">Use Default</option>
					{#each AI_PROVIDERS as p}
						<option value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
					{/each}
				</select>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					Leave empty to use your account's default provider
				</p>
			</div>

			<!-- Model Selection -->
			<div>
				<label for="ai-model" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					Model
				</label>
				<div class="relative">
					<input
						id="ai-model"
						type="text"
						bind:value={model}
						list="model-suggestions"
						placeholder={provider ? `e.g., ${modelSuggestions[0] ?? 'model name'}` : 'Use default model'}
						class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
					/>
					<datalist id="model-suggestions">
						{#each modelSuggestions as suggestion}
							<option value={suggestion}>{suggestion}</option>
						{/each}
					</datalist>
				</div>
				{#if provider && modelSuggestions.length > 0}
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						Suggested: {modelSuggestions.slice(0, 3).join(', ')}
					</p>
				{/if}
			</div>

			<!-- Temperature Slider -->
			<div>
				<label for="ai-temperature" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
					Temperature: <span class="font-mono text-indigo-600 dark:text-indigo-400">{displayTemperature.toFixed(2)}</span>
				</label>
				<input
					id="ai-temperature"
					type="range"
					min={tempRange.min}
					max={tempRange.max}
					step="0.05"
					value={displayTemperature}
					on:input={handleTemperatureChange}
					class="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-indigo-600"
				/>
				<div class="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
					<span>Focused ({tempRange.min})</span>
					<span>Creative ({tempRange.max})</span>
				</div>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					Lower = more deterministic, Higher = more creative/random
				</p>
			</div>

			<!-- Reset Button -->
			{#if provider || model || temperature !== null}
				<button
					type="button"
					on:click={() => {
						provider = null;
						model = '';
						temperature = null;
					}}
					class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-800 dark:hover:text-indigo-300"
				>
					Reset to defaults
				</button>
			{/if}
		</div>
	{/if}
</div>
