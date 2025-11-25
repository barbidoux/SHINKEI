<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { api } from '$lib/api';
	import type {
		CharacterRelationshipResponse,
		CharacterRelationshipListResponse,
		RelationshipStrength
	} from '$lib/types/relationship';
	import type { CharacterResponse } from '$lib/types/character';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import Button from '$lib/components/Button.svelte';
	import RelationshipCard from '$lib/components/RelationshipCard.svelte';

	const worldId = $page.params.id as string;

	let relationships: CharacterRelationshipResponse[] = [];
	let characters: Map<string, CharacterResponse> = new Map();
	let total = 0;
	let loading = true;
	let error = '';

	// Filters
	let strengthFilter: RelationshipStrength | 'all' = 'all';
	let relationshipTypeFilter = '';
	let currentPage = 1;
	let pageSize = 20;

	$: skip = (currentPage - 1) * pageSize;
	$: totalPages = Math.ceil(total / pageSize);

	onMount(() => {
		loadRelationships();
	});

	async function loadRelationships() {
		loading = true;
		error = '';

		try {
			const params = new URLSearchParams({
				skip: skip.toString(),
				limit: pageSize.toString()
			});

			if (strengthFilter !== 'all') params.append('strength', strengthFilter);
			if (relationshipTypeFilter) params.append('relationship_type', relationshipTypeFilter);

			const response = await api.get<CharacterRelationshipListResponse>(
				`/worlds/${worldId}/character-relationships?${params}`
			);

			relationships = response.relationships;
			total = response.total;

			// Load character names for display
			await loadCharacterNames();
		} catch (e: any) {
			error = e.message || 'Failed to load relationships';
			console.error('Error loading relationships:', e);
		} finally {
			loading = false;
		}
	}

	async function loadCharacterNames() {
		// Get unique character IDs
		const characterIds = new Set<string>();
		relationships.forEach((rel) => {
			characterIds.add(rel.character_a_id);
			characterIds.add(rel.character_b_id);
		});

		// Load characters (assuming they're already loaded or fetch them)
		try {
			const response = await api.get<{ characters: CharacterResponse[]; total: number }>(
				`/worlds/${worldId}/characters?limit=1000`
			);

			characters = new Map(response.characters.map((c) => [c.id, c]));
		} catch (e: any) {
			console.error('Error loading character names:', e);
		}
	}

	function handleFilterChange() {
		currentPage = 1; // Reset to first page when filters change
		loadRelationships();
	}

	function handlePageChange(newPage: number) {
		currentPage = newPage;
		loadRelationships();
	}

	function getCharacterName(characterId: string): string {
		return characters.get(characterId)?.name || 'Unknown';
	}
</script>

<svelte:head>
	<title>Character Relationships - SHINKEI</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Breadcrumb -->
	<Breadcrumb
		items={[
			{ label: 'Worlds', href: '/worlds' },
			{ label: 'World', href: `/worlds/${worldId}` },
			{ label: 'Relationships', href: `/worlds/${worldId}/relationships` }
		]}
	/>

	<!-- Header -->
	<div class="flex items-center justify-between mb-8">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Character Relationships</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				Manage connections between characters in your world
			</p>
		</div>
		<div class="flex items-center gap-3">
			<Button href="/worlds/{worldId}/relationships/graph" variant="secondary">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4 inline-block mr-1"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
					/>
				</svg>
				View Graph
			</Button>
			<Button href="/worlds/{worldId}/relationships/new">+ New Relationship</Button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" text="Loading relationships..." />
		</div>
	{:else if error}
		<div class="text-center py-12">
			<p class="text-red-500 dark:text-red-400">{error}</p>
		</div>
	{:else}
		<!-- Main Content Grid -->
		<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
			<!-- Filters Sidebar -->
			<div class="lg:col-span-1">
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 space-y-4">
					<div class="flex items-center justify-between">
						<h3 class="text-lg font-semibold text-gray-900 dark:text-white">Filters</h3>
						{#if strengthFilter !== 'all' || relationshipTypeFilter}
							<button
								type="button"
								on:click={() => {
									strengthFilter = 'all';
									relationshipTypeFilter = '';
									handleFilterChange();
								}}
								class="text-sm text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
							>
								Clear
							</button>
						{/if}
					</div>

					<!-- Strength Filter -->
					<div>
						<label for="strength-filter" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Strength
						</label>
						<select
							id="strength-filter"
							bind:value={strengthFilter}
							on:change={handleFilterChange}
							class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
						>
							<option value="all">All Strengths</option>
							<option value="strong">Strong</option>
							<option value="moderate">Moderate</option>
							<option value="weak">Weak</option>
						</select>
					</div>

					<!-- Type Filter -->
					<div>
						<label for="type-filter" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Relationship Type
						</label>
						<input
							type="text"
							id="type-filter"
							bind:value={relationshipTypeFilter}
							on:input={handleFilterChange}
							placeholder="e.g., friendship, romantic"
							class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
						/>
					</div>
				</div>

				<!-- Summary Card -->
				<div class="mt-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
					<h3 class="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">Summary</h3>
					<p class="text-sm text-blue-700 dark:text-blue-300">
						{total} relationship{total !== 1 ? 's' : ''} total
					</p>
					<p class="text-xs text-blue-600 dark:text-blue-400 mt-1">
						Page {currentPage} of {totalPages || 1}
					</p>
				</div>
			</div>

			<!-- Relationships Content -->
			<div class="lg:col-span-3">
				{#if relationships.length === 0}
					<div class="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-16 w-16 mx-auto text-gray-400 mb-4"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
							/>
						</svg>
						<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
							No relationships yet
						</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
							{strengthFilter !== 'all' || relationshipTypeFilter
								? 'No relationships match your filters.'
								: 'Get started by creating your first character relationship.'}
						</p>
						{#if !(strengthFilter !== 'all' || relationshipTypeFilter)}
							<Button href="/worlds/{worldId}/relationships/new">Create Relationship</Button>
						{/if}
					</div>
				{:else}
					<!-- Grid View -->
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						{#each relationships as relationship (relationship.id)}
							<RelationshipCard
								{relationship}
								{worldId}
								characterAName={getCharacterName(relationship.character_a_id)}
								characterBName={getCharacterName(relationship.character_b_id)}
							/>
						{/each}
					</div>

					<!-- Pagination -->
					{#if totalPages > 1}
						<div class="mt-6 flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg shadow px-4 py-3">
							<div class="text-sm text-gray-700 dark:text-gray-300">
								Showing {skip + 1} to {Math.min(skip + pageSize, total)} of {total} relationships
							</div>
							<div class="flex items-center gap-2">
								<button
									type="button"
									on:click={() => handlePageChange(currentPage - 1)}
									disabled={currentPage === 1}
									class="px-3 py-1 rounded-md text-sm font-medium bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
								>
									Previous
								</button>
								<span class="text-sm text-gray-700 dark:text-gray-300">
									Page {currentPage} of {totalPages}
								</span>
								<button
									type="button"
									on:click={() => handlePageChange(currentPage + 1)}
									disabled={currentPage === totalPages}
									class="px-3 py-1 rounded-md text-sm font-medium bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
								>
									Next
								</button>
							</div>
						</div>
					{/if}
				{/if}
			</div>
		</div>
	{/if}
</div>
