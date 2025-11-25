<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { generateLocationSuggestions } from '$lib/api/entity-generation';
	import type { LocationResponse, LocationListResponse, LocationSignificance } from '$lib/types/location';
	import type { EntitySuggestion, AIProvider } from '$lib/types/entity-generation';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import Button from '$lib/components/Button.svelte';
	import LocationCard from '$lib/components/LocationCard.svelte';
	import LocationFilters from '$lib/components/LocationFilters.svelte';
	import LocationHierarchyTree from '$lib/components/LocationHierarchyTree.svelte';
	import AIGenerationOptions from '$lib/components/AIGenerationOptions.svelte';

	const worldId = $page.params.id as string;

	let locations: LocationResponse[] = [];
	let total = 0;
	let loading = true;
	let error = '';

	// View mode: 'grid' or 'hierarchy'
	let viewMode: 'grid' | 'hierarchy' = 'grid';

	// Filters
	let locationType: string | null = null;
	let search: string = '';
	let currentPage = 1;
	let pageSize = 20;

	// AI Generation state
	let showAIInputModal = false;
	let showAIResultsModal = false;
	let aiGenerating = false;
	let aiError = '';
	let aiSuggestions: EntitySuggestion[] = [];

	// AI Generation options
	let aiProvider: AIProvider | null = null;
	let aiModel: string = '';
	let aiTemperature: number | null = null;
	let aiUserPrompt: string = '';
	let aiLocationType: string = '';
	let aiSignificance: LocationSignificance | null = null;
	let aiParentLocationId: string | null = null;
	let aiOptionsExpanded: boolean = false;

	$: skip = (currentPage - 1) * pageSize;
	$: totalPages = Math.ceil(total / pageSize);

	// Build location map for parent lookups
	$: locationMap = new Map(locations.map((loc) => [loc.id, loc]));

	onMount(() => {
		loadLocations();
	});

	async function loadLocations() {
		loading = true;
		error = '';

		try {
			const params = new URLSearchParams({
				skip: skip.toString(),
				limit: pageSize.toString()
			});

			if (locationType) params.append('location_type', locationType);
			if (search) params.append('search', search);

			const response = await api.get<LocationListResponse>(
				`/worlds/${worldId}/locations?${params}`
			);

			locations = response.locations;
			total = response.total;
		} catch (e: any) {
			error = e.message || 'Failed to load locations';
			console.error('Error loading locations:', e);
		} finally {
			loading = false;
		}
	}

	function handleFilterChange() {
		currentPage = 1; // Reset to first page when filters change
		loadLocations();
	}

	function handlePageChange(newPage: number) {
		currentPage = newPage;
		loadLocations();
	}

	function openAIGenerationModal() {
		// Pre-fill with current filter values
		aiLocationType = locationType ?? '';
		aiUserPrompt = search;
		showAIInputModal = true;
	}

	async function generateWithAI() {
		aiGenerating = true;
		aiError = '';
		aiSuggestions = [];

		try {
			const response = await generateLocationSuggestions(worldId, {
				location_type: aiLocationType || undefined,
				significance: aiSignificance ?? undefined,
				parent_location_id: aiParentLocationId ?? undefined,
				user_prompt: aiUserPrompt || undefined,
				provider: aiProvider ?? undefined,
				model: aiModel || undefined,
				temperature: aiTemperature ?? undefined
			});

			aiSuggestions = response.suggestions;
			showAIInputModal = false;
			showAIResultsModal = true;
		} catch (e: any) {
			aiError = e.message || 'Failed to generate locations';
		} finally {
			aiGenerating = false;
		}
	}

	function createLocationFromSuggestion(suggestion: EntitySuggestion) {
		// Navigate to new location page with pre-filled data
		const params = new URLSearchParams({
			name: suggestion.name,
			description: suggestion.description || '',
			location_type: suggestion.metadata?.location_type || aiLocationType || '',
			significance: suggestion.metadata?.significance || 'background'
		});
		if (aiParentLocationId) {
			params.append('parent_location_id', aiParentLocationId);
		}
		goto(`/worlds/${worldId}/locations/new?${params}`);
	}
</script>

<svelte:head>
	<title>Locations - SHINKEI</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Breadcrumb -->
	<Breadcrumb
		items={[
			{ label: 'Worlds', href: '/worlds' },
			{ label: 'World', href: `/worlds/${worldId}` },
			{ label: 'Locations', href: `/worlds/${worldId}/locations` }
		]}
	/>

	<!-- Header -->
	<div class="flex items-center justify-between mb-8">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Locations</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				Manage places, buildings, and areas in your world
			</p>
		</div>
		<div class="flex items-center gap-3">
			<Button
				variant="secondary"
				on:click={openAIGenerationModal}
				disabled={aiGenerating}
			>
				{#if aiGenerating}
					Generating...
				{:else}
					Generate with AI
				{/if}
			</Button>
			<Button href="/worlds/{worldId}/locations/new">+ New Location</Button>
		</div>
	</div>

	<!-- View Mode Toggle -->
	<div class="mb-6 flex items-center gap-2 bg-white dark:bg-gray-800 rounded-lg shadow p-2 w-fit">
		<button
			type="button"
			on:click={() => (viewMode = 'grid')}
			class="px-4 py-2 rounded-md text-sm font-medium transition-colors {viewMode === 'grid'
				? 'bg-indigo-600 text-white'
				: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-5 w-5 inline-block mr-1"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
				/>
			</svg>
			Grid View
		</button>
		<button
			type="button"
			on:click={() => (viewMode = 'hierarchy')}
			class="px-4 py-2 rounded-md text-sm font-medium transition-colors {viewMode === 'hierarchy'
				? 'bg-indigo-600 text-white'
				: 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'}"
		>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-5 w-5 inline-block mr-1"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
				/>
			</svg>
			Hierarchy View
		</button>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" text="Loading locations..." />
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
				<LocationFilters
					bind:locationType
					bind:search
					onFilterChange={handleFilterChange}
				/>

				<!-- Summary Card -->
				<div class="mt-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
					<h3 class="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">Summary</h3>
					<p class="text-sm text-blue-700 dark:text-blue-300">
						{total} location{total !== 1 ? 's' : ''} total
					</p>
					{#if viewMode === 'hierarchy'}
						<p class="text-xs text-blue-600 dark:text-blue-400 mt-1">
							Showing hierarchical structure
						</p>
					{:else}
						<p class="text-xs text-blue-600 dark:text-blue-400 mt-1">
							Page {currentPage} of {totalPages || 1}
						</p>
					{/if}
				</div>
			</div>

			<!-- Locations Content -->
			<div class="lg:col-span-3">
				{#if locations.length === 0}
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
								d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
							/>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
							/>
						</svg>
						<h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">No locations yet</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
							Get started by creating your first location.
						</p>
						<Button href="/worlds/{worldId}/locations/new">Create Location</Button>
					</div>
				{:else if viewMode === 'hierarchy'}
					<!-- Hierarchy Tree View -->
					<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
						<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
							Location Hierarchy
						</h2>
						<LocationHierarchyTree {locations} {worldId} />
					</div>
				{:else}
					<!-- Grid View -->
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						{#each locations as location (location.id)}
							<LocationCard
								{location}
								{worldId}
								showParent={true}
								parentLocation={location.parent_location_id
									? locationMap.get(location.parent_location_id)
									: undefined}
							/>
						{/each}
					</div>

					<!-- Pagination -->
					{#if totalPages > 1}
						<div class="mt-6 flex items-center justify-between bg-white dark:bg-gray-800 rounded-lg shadow px-4 py-3">
							<div class="text-sm text-gray-700 dark:text-gray-300">
								Showing {skip + 1} to {Math.min(skip + pageSize, total)} of {total} locations
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

<!-- AI Input Modal - Configure generation options -->
{#if showAIInputModal}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 bg-black/50 z-40 transition-opacity"
		on:click={() => showAIInputModal = false}
		on:keydown={(e) => e.key === 'Escape' && (showAIInputModal = false)}
		role="button"
		tabindex="0"
	></div>

	<!-- Modal -->
	<div class="fixed inset-0 z-50 overflow-y-auto">
		<div class="flex min-h-full items-center justify-center p-4">
			<div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-lg w-full">
				<!-- Header -->
				<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
					<h2 class="text-xl font-bold text-gray-900 dark:text-white">
						Generate Locations with AI
					</h2>
					<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
						Configure AI generation settings
					</p>
				</div>

				<!-- Content -->
				<div class="px-6 py-4 space-y-4 max-h-[60vh] overflow-y-auto">
					{#if aiError}
						<div class="rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
							<p class="text-sm text-red-800 dark:text-red-200">{aiError}</p>
						</div>
					{/if}

					<!-- User Prompt -->
					<div>
						<label for="ai-user-prompt" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Prompt (optional)
						</label>
						<textarea
							id="ai-user-prompt"
							bind:value={aiUserPrompt}
							placeholder="Describe the kind of location you want to generate... e.g., 'a hidden underground bunker with advanced technology'"
							rows="3"
							class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
						></textarea>
					</div>

					<!-- Location Type -->
					<div>
						<label for="ai-location-type" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Location Type (optional)
						</label>
						<input
							id="ai-location-type"
							type="text"
							bind:value={aiLocationType}
							placeholder="e.g., city, building, forest, room"
							class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
						/>
					</div>

					<!-- Significance -->
					<div>
						<label for="ai-significance" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Significance
						</label>
						<select
							id="ai-significance"
							bind:value={aiSignificance}
							class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
						>
							<option value={null}>Any significance</option>
							<option value="major">Major</option>
							<option value="minor">Minor</option>
							<option value="background">Background</option>
						</select>
					</div>

					<!-- Parent Location -->
					{#if locations.length > 0}
						<div>
							<label for="ai-parent-location" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
								Parent Location (optional)
							</label>
							<select
								id="ai-parent-location"
								bind:value={aiParentLocationId}
								class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
							>
								<option value={null}>No parent (top-level location)</option>
								{#each locations as loc}
									<option value={loc.id}>{loc.name}</option>
								{/each}
							</select>
							<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
								Generate as a sub-location of an existing place
							</p>
						</div>
					{/if}

					<!-- AI Generation Options -->
					<AIGenerationOptions
						bind:provider={aiProvider}
						bind:model={aiModel}
						bind:temperature={aiTemperature}
						bind:expanded={aiOptionsExpanded}
					/>
				</div>

				<!-- Footer -->
				<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
					<Button
						variant="secondary"
						on:click={() => showAIInputModal = false}
					>
						Cancel
					</Button>
					<Button
						on:click={generateWithAI}
						disabled={aiGenerating}
					>
						{#if aiGenerating}
							<svg class="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
								<circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
								<path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
							</svg>
							Generating...
						{:else}
							Generate Locations
						{/if}
					</Button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- AI Results Modal -->
{#if showAIResultsModal}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 bg-black/50 z-40 transition-opacity"
		on:click={() => showAIResultsModal = false}
		on:keydown={(e) => e.key === 'Escape' && (showAIResultsModal = false)}
		role="button"
		tabindex="0"
	></div>

	<!-- Modal -->
	<div class="fixed inset-0 z-50 overflow-y-auto">
		<div class="flex min-h-full items-center justify-center p-4">
			<div class="relative bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-3xl w-full max-h-[80vh] overflow-hidden">
				<!-- Header -->
				<div class="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
					<h2 class="text-xl font-bold text-gray-900 dark:text-white">
						AI-Generated Location Suggestions
					</h2>
					<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
						Select a location to create or modify the suggestions
					</p>
				</div>

				<!-- Content -->
				<div class="px-6 py-4 overflow-y-auto max-h-[60vh]">
					{#if aiError}
						<div class="rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
							<p class="text-sm text-red-800 dark:text-red-200">{aiError}</p>
						</div>
					{:else if aiSuggestions.length === 0}
						<div class="text-center py-8">
							<p class="text-gray-500 dark:text-gray-400">No suggestions generated</p>
						</div>
					{:else}
						<div class="space-y-4">
							{#each aiSuggestions as suggestion}
								<div class="border-2 border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors">
									<div class="flex items-start justify-between">
										<div class="flex-1">
											<div class="flex items-center gap-2 mb-2">
												<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
													{suggestion.name}
												</h3>
												<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200">
													{Math.round(suggestion.confidence * 100)}% confidence
												</span>
												{#if suggestion.metadata?.location_type}
													<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
														{suggestion.metadata.location_type}
													</span>
												{/if}
												{#if suggestion.metadata?.significance}
													<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
														{suggestion.metadata.significance}
													</span>
												{/if}
											</div>

											{#if suggestion.description}
												<p class="text-sm text-gray-700 dark:text-gray-300 mb-3">
													{suggestion.description}
												</p>
											{/if}

											{#if suggestion.metadata}
												<div class="space-y-1 text-sm">
													{#if suggestion.metadata.atmosphere}
														<p class="text-gray-600 dark:text-gray-400">
															<span class="font-medium">Atmosphere:</span> {suggestion.metadata.atmosphere}
														</p>
													{/if}
													{#if suggestion.metadata.notable_features}
														<p class="text-gray-600 dark:text-gray-400">
															<span class="font-medium">Features:</span>
															{Array.isArray(suggestion.metadata.notable_features)
																? suggestion.metadata.notable_features.join(', ')
																: suggestion.metadata.notable_features}
														</p>
													{/if}
												</div>
											{/if}
										</div>

										<Button
											size="sm"
											on:click={() => createLocationFromSuggestion(suggestion)}
										>
											Create Location
										</Button>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Footer -->
				<div class="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
					<Button
						variant="secondary"
						on:click={() => showAIResultsModal = false}
					>
						Close
					</Button>
					<Button
						variant="secondary"
						on:click={() => {
							showAIResultsModal = false;
							showAIInputModal = true;
						}}
					>
						Modify Options
					</Button>
					<Button
						on:click={generateWithAI}
						disabled={aiGenerating}
					>
						{#if aiGenerating}
							Regenerating...
						{:else}
							Regenerate
						{/if}
					</Button>
				</div>
			</div>
		</div>
	</div>
{/if}
