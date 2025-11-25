<script lang="ts">
	import type { EntityImportance } from '$lib/types/character';
	import { ENTITY_IMPORTANCE_OPTIONS } from '$lib/types/character';

	export let importance: EntityImportance | null = null;
	export let search: string = '';
	export let onFilterChange: () => void = () => {};

	function handleImportanceChange(e: Event) {
		const target = e.target as HTMLSelectElement;
		importance = target.value === '' ? null : (target.value as EntityImportance);
		onFilterChange();
	}

	function handleSearchChange() {
		onFilterChange();
	}

	function clearFilters() {
		importance = null;
		search = '';
		onFilterChange();
	}

	$: hasFilters = importance !== null || search !== '';
</script>

<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-4">
	<div class="flex items-center justify-between">
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Filters</h3>
		{#if hasFilters}
			<button
				type="button"
				on:click={clearFilters}
				class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
			>
				Clear all
			</button>
		{/if}
	</div>

	<!-- Search -->
	<div>
		<label for="character-search" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
			Search
		</label>
		<input
			type="text"
			id="character-search"
			bind:value={search}
			on:input={handleSearchChange}
			placeholder="Search by name, role, or description..."
			class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
		/>
	</div>

	<!-- Importance Filter -->
	<div>
		<label for="importance-filter" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
			Importance
		</label>
		<select
			id="importance-filter"
			value={importance ?? ''}
			on:change={handleImportanceChange}
			class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
		>
			<option value="">All Characters</option>
			{#each ENTITY_IMPORTANCE_OPTIONS as option}
				<option value={option.value}>{option.label}</option>
			{/each}
		</select>
	</div>

	<!-- Active Filters Summary -->
	{#if hasFilters}
		<div class="pt-2 border-t border-gray-200 dark:border-gray-700">
			<p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Active filters:</p>
			<div class="flex flex-wrap gap-2">
				{#if importance}
					<span
						class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200"
					>
						{ENTITY_IMPORTANCE_OPTIONS.find((o) => o.value === importance)?.label}
					</span>
				{/if}
				{#if search}
					<span
						class="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200"
					>
						Search: "{search.length > 20 ? search.substring(0, 20) + '...' : search}"
					</span>
				{/if}
			</div>
		</div>
	{/if}
</div>
