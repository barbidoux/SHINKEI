<script lang="ts">
	import type { CharacterResponse } from '$lib/types/character';
	import type { LocationResponse } from '$lib/types/location';

	type Entity = CharacterResponse | LocationResponse;

	export let entities: Entity[] = [];
	export let entityType: 'character' | 'location';
	export let onSearchChange: (filtered: Entity[]) => void;

	let searchQuery = '';
	let searchFields: string[] =
		entityType === 'character'
			? ['name', 'description', 'role']
			: ['name', 'description', 'location_type'];

	$: searchFieldOptions =
		entityType === 'character'
			? [
					{ value: 'name', label: 'Name' },
					{ value: 'description', label: 'Description' },
					{ value: 'role', label: 'Role' }
			  ]
			: [
					{ value: 'name', label: 'Name' },
					{ value: 'description', label: 'Description' },
					{ value: 'location_type', label: 'Type' }
			  ];

	// Apply search whenever query or fields change
	$: {
		applySearch();
	}

	function applySearch() {
		if (!searchQuery.trim()) {
			onSearchChange(entities);
			return;
		}

		const query = searchQuery.toLowerCase().trim();
		const filtered = entities.filter((entity) => {
			// Check name
			if (searchFields.includes('name') && entity.name?.toLowerCase().includes(query)) {
				return true;
			}

			// Check description
			if (
				searchFields.includes('description') &&
				entity.description?.toLowerCase().includes(query)
			) {
				return true;
			}

			// Character-specific: check role
			if (entityType === 'character' && searchFields.includes('role')) {
				const char = entity as CharacterResponse;
				if (char.role?.toLowerCase().includes(query)) {
					return true;
				}
			}

			// Location-specific: check location_type
			if (entityType === 'location' && searchFields.includes('location_type')) {
				const loc = entity as LocationResponse;
				if (loc.location_type?.toLowerCase().includes(query)) {
					return true;
				}
			}

			return false;
		});

		onSearchChange(filtered);
	}

	function toggleSearchField(field: string) {
		if (searchFields.includes(field)) {
			// Don't allow removing all fields
			if (searchFields.length > 1) {
				searchFields = searchFields.filter((f) => f !== field);
			}
		} else {
			searchFields = [...searchFields, field];
		}
	}

	function clearSearch() {
		searchQuery = '';
		searchFields =
			entityType === 'character'
				? ['name', 'description', 'role']
				: ['name', 'description', 'location_type'];
	}
</script>

<div class="entity-search">
	<!-- Search Input -->
	<div class="relative">
		<div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
			<svg
				class="h-5 w-5 text-gray-400 dark:text-gray-500"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
				/>
			</svg>
		</div>
		<input
			type="text"
			bind:value={searchQuery}
			placeholder="Search {entityType}s..."
			class="block w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-md leading-5 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:placeholder-gray-400 dark:focus:placeholder-gray-500 focus:ring-1 focus:ring-indigo-500 dark:focus:ring-indigo-400 focus:border-indigo-500 dark:focus:border-indigo-400 sm:text-sm"
		/>
		{#if searchQuery}
			<div class="absolute inset-y-0 right-0 pr-3 flex items-center">
				<button
					on:click={clearSearch}
					class="text-gray-400 dark:text-gray-500 hover:text-gray-500 dark:hover:text-gray-400"
					aria-label="Clear search"
				>
					<svg class="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
						<path
							fill-rule="evenodd"
							d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
							clip-rule="evenodd"
						/>
					</svg>
				</button>
			</div>
		{/if}
	</div>

	<!-- Search Fields Toggle -->
	<div class="mt-2">
		<div class="flex items-center gap-2 text-xs flex-wrap">
			<span class="text-gray-500 dark:text-gray-400">Search in:</span>
			{#each searchFieldOptions as option}
				<button
					type="button"
					on:click={() => toggleSearchField(option.value)}
					class="px-2 py-1 rounded-md font-medium transition-colors {searchFields.includes(
						option.value
					)
						? 'bg-indigo-100 dark:bg-indigo-900 text-indigo-700 dark:text-indigo-200 border border-indigo-200 dark:border-indigo-700'
						: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-600 hover:bg-gray-200 dark:hover:bg-gray-600'}"
				>
					{option.label}
				</button>
			{/each}
		</div>
	</div>

	<!-- Search Results Summary -->
	{#if searchQuery}
		<div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
			{#if entities.length === 0}
				No {entityType}s to search
			{:else}
				<span>
					Searching {entities.length}
					{entities.length === 1 ? entityType : `${entityType}s`}
				</span>
			{/if}
		</div>
	{/if}
</div>

<style>
	.entity-search {
		width: 100%;
	}
</style>
