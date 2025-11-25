<script lang="ts">
	import { api } from '$lib/api';
	import { onMount } from 'svelte';
	import type { CharacterResponse } from '$lib/types/character';
	import type { LocationResponse } from '$lib/types/location';
	import { ENTITY_IMPORTANCE_COLORS } from '$lib/types/character';
	import { LOCATION_TYPE_COLORS } from '$lib/types/location';

	export let worldId: string;
	export let entityType: 'character' | 'location';
	export let selectedEntityId: string = '';
	export let onSelect: (entityId: string) => void = () => {};
	export let placeholder: string = '';
	export let excludeEntityId: string = ''; // Exclude specific entity (e.g., prevent self-selection)

	type Entity = CharacterResponse | LocationResponse;

	let entities: Entity[] = [];
	let loading: boolean = false;
	let error: string = '';
	let searchQuery: string = '';
	let selectedFilter: string = 'all';
	let showPicker: boolean = false;

	$: filteredEntities = entities.filter((entity) => {
		// Exclude the specified entity
		if (excludeEntityId && entity.id === excludeEntityId) {
			return false;
		}

		const matchesSearch =
			searchQuery === '' ||
			entity.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
			(entity.description?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);

		let matchesFilter = true;
		if (entityType === 'character') {
			const char = entity as CharacterResponse;
			matchesFilter = selectedFilter === 'all' || char.importance === selectedFilter;
		} else {
			const loc = entity as LocationResponse;
			matchesFilter = selectedFilter === 'all' || loc.location_type === selectedFilter;
		}

		return matchesSearch && matchesFilter;
	});

	$: filterOptions =
		entityType === 'character'
			? ['all', 'major', 'minor', 'background']
			: [
					'all',
					...new Set(
						(entities as LocationResponse[])
							.map((e) => e.location_type)
							.filter((t) => t) as string[]
					)
			  ];

	$: selectedEntity = entities.find((e) => e.id === selectedEntityId);

	$: defaultPlaceholder =
		entityType === 'character' ? 'Select Character' : 'Select Location';

	onMount(async () => {
		await loadEntities();
	});

	async function loadEntities() {
		loading = true;
		error = '';
		try {
			const endpoint =
				entityType === 'character'
					? `/worlds/${worldId}/characters?limit=1000`
					: `/worlds/${worldId}/locations?limit=1000`;

			const response = await api.get<{
				characters?: Entity[];
				locations?: Entity[];
				total: number;
			}>(endpoint);

			entities =
				entityType === 'character'
					? (response.characters as Entity[])
					: (response.locations as Entity[]);
		} catch (e: any) {
			error = e.message || `Failed to load ${entityType}s`;
			console.error(`Failed to load ${entityType}s:`, e);
		} finally {
			loading = false;
		}
	}

	function selectEntity(entityId: string) {
		selectedEntityId = entityId;
		onSelect(entityId);
		showPicker = false;
	}

	function clearSelection() {
		selectedEntityId = '';
		onSelect('');
	}

	function getEntityBadgeColor(entity: Entity): string {
		if (entityType === 'character') {
			const char = entity as CharacterResponse;
			return ENTITY_IMPORTANCE_COLORS[char.importance] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
		} else {
			const loc = entity as LocationResponse;
			return loc.location_type && LOCATION_TYPE_COLORS[loc.location_type]
				? LOCATION_TYPE_COLORS[loc.location_type]
				: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
		}
	}

	function getEntityLabel(entity: Entity): string {
		if (entityType === 'character') {
			return (entity as CharacterResponse).importance;
		} else {
			return (entity as LocationResponse).location_type || 'location';
		}
	}

	function getEntitySecondaryInfo(entity: Entity): string {
		if (entityType === 'character') {
			return (entity as CharacterResponse).role || '';
		} else {
			return '';
		}
	}
</script>

<div class="entity-picker">
	<!-- Selected Entity Display (Compact) -->
	{#if selectedEntity}
		<div
			class="mb-2 p-3 bg-green-50 dark:bg-green-900/20 rounded-md border border-green-200 dark:border-green-700"
		>
			<div class="flex items-start justify-between">
				<div class="flex-1 min-w-0">
					<div class="flex items-center gap-2 mb-1">
						<span
							class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {getEntityBadgeColor(
								selectedEntity
							)}"
						>
							{getEntityLabel(selectedEntity)}
						</span>
						{#if getEntitySecondaryInfo(selectedEntity)}
							<span class="text-xs text-gray-600 dark:text-gray-400">
								{getEntitySecondaryInfo(selectedEntity)}
							</span>
						{/if}
					</div>
					<p class="text-sm text-gray-900 dark:text-gray-100 truncate">
						{selectedEntity.name}
					</p>
				</div>
				<button
					type="button"
					on:click={clearSelection}
					class="ml-2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
					title="Clear selection"
				>
					<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M6 18L18 6M6 6l12 12"
						/>
					</svg>
				</button>
			</div>
		</div>
	{/if}

	<!-- Picker Toggle Button -->
	<button
		type="button"
		on:click={() => (showPicker = !showPicker)}
		class="w-full px-3 py-2 text-sm rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 flex items-center justify-between"
	>
		<span>
			{selectedEntity ? `Change ${entityType}` : placeholder || defaultPlaceholder}
		</span>
		<svg
			class="w-4 h-4 transition-transform {showPicker ? 'rotate-180' : ''}"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	<!-- Entity Picker Panel -->
	{#if showPicker}
		<div
			class="mt-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 shadow-lg max-h-96 overflow-hidden flex flex-col"
		>
			<!-- Search and Filter Controls -->
			<div class="p-3 border-b border-gray-200 dark:border-gray-700 space-y-2">
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search {entityType}s..."
					class="w-full px-3 py-2 text-sm rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
				/>
				<select
					bind:value={selectedFilter}
					class="w-full px-3 py-2 text-sm rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
				>
					{#each filterOptions as option}
						<option value={option}>
							{option === 'all'
								? entityType === 'character'
									? 'All Importance'
									: 'All Types'
								: option.charAt(0).toUpperCase() + option.slice(1)}
						</option>
					{/each}
				</select>
			</div>

			<!-- Entity List -->
			<div class="flex-1 overflow-y-auto">
				{#if loading}
					<div class="p-4 text-center text-gray-500 dark:text-gray-400">
						<svg
							class="animate-spin h-5 w-5 mx-auto mb-2"
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
						>
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
							></circle>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							></path>
						</svg>
						Loading {entityType}s...
					</div>
				{:else if error}
					<div class="p-4 text-center text-red-600 dark:text-red-400">
						{error}
					</div>
				{:else if filteredEntities.length === 0}
					<div class="p-4 text-center text-gray-500 dark:text-gray-400">
						{searchQuery || selectedFilter !== 'all'
							? `No ${entityType}s match your filters`
							: `No ${entityType}s found`}
					</div>
				{:else}
					<div class="divide-y divide-gray-200 dark:divide-gray-700">
						{#each filteredEntities as entity}
							<button
								type="button"
								on:click={() => selectEntity(entity.id)}
								class="w-full p-3 text-left hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors {entity.id ===
								selectedEntityId
									? 'bg-blue-50 dark:bg-blue-900/20'
									: ''}"
							>
								<div class="flex items-start justify-between gap-2">
									<div class="flex-1 min-w-0">
										<div class="flex items-center gap-2 mb-1">
											<span
												class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {getEntityBadgeColor(
													entity
												)}"
											>
												{getEntityLabel(entity)}
											</span>
											{#if getEntitySecondaryInfo(entity)}
												<span class="text-xs text-gray-600 dark:text-gray-400">
													{getEntitySecondaryInfo(entity)}
												</span>
											{/if}
										</div>
										<p class="text-sm font-medium text-gray-900 dark:text-gray-100 mb-1">
											{entity.name}
										</p>
										{#if entity.description}
											<p class="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
												{entity.description}
											</p>
										{/if}
									</div>
									{#if entity.id === selectedEntityId}
										<svg
											class="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0"
											fill="currentColor"
											viewBox="0 0 20 20"
										>
											<path
												fill-rule="evenodd"
												d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
												clip-rule="evenodd"
											/>
										</svg>
									{/if}
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer -->
			<div
				class="p-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50 text-xs text-gray-600 dark:text-gray-400 text-center"
			>
				{filteredEntities.length} of {entities.length}
				{entityType}s
			</div>
		</div>
	{/if}
</div>

<style>
	.entity-picker {
		position: relative;
	}
</style>
