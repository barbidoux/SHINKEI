<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { generateCharacterSuggestions } from '$lib/api/entity-generation';
	import type {
		CharacterListResponse,
		CharacterResponse,
		EntityImportance
	} from '$lib/types/character';
	import type { EntitySuggestion, AIProvider } from '$lib/types/entity-generation';
	import CharacterCard from '$lib/components/CharacterCard.svelte';
	import CharacterFilters from '$lib/components/CharacterFilters.svelte';
	import Button from '$lib/components/Button.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import AIGenerationOptions from '$lib/components/AIGenerationOptions.svelte';

	const worldId = $page.params.id as string;

	let characters: CharacterResponse[] = [];
	let total = 0;
	let loading = true;
	let error = '';
	let showAIGenerationModal = false;
	let showAIInputModal = false;
	let aiGenerating = false;
	let aiError = '';
	let aiSuggestions: EntitySuggestion[] = [];

	// AI Generation options
	let aiProvider: AIProvider | null = null;
	let aiModel: string = '';
	let aiTemperature: number | null = null;
	let aiUserPrompt: string = '';
	let aiImportance: EntityImportance | null = null;
	let aiOptionsExpanded: boolean = false;

	// Filters
	let importance: EntityImportance | null = null;
	let search: string = '';
	let currentPage = 1;
	let pageSize = 20;

	$: skip = (currentPage - 1) * pageSize;
	$: totalPages = Math.ceil(total / pageSize);

	async function loadCharacters() {
		loading = true;
		error = '';

		try {
			const params = new URLSearchParams({
				skip: skip.toString(),
				limit: pageSize.toString()
			});

			if (importance) params.append('importance', importance);
			if (search) params.append('search', search);

			const response = await api.get<CharacterListResponse>(
				`/worlds/${worldId}/characters?${params}`
			);

			characters = response.characters;
			total = response.total;
		} catch (e: any) {
			error = e.message || 'Failed to load characters';
			console.error('Error loading characters:', e);
		} finally {
			loading = false;
		}
	}

	function handleFilterChange() {
		currentPage = 1; // Reset to first page when filters change
		loadCharacters();
	}

	function handlePreviousPage() {
		if (currentPage > 1) {
			currentPage--;
			loadCharacters();
		}
	}

	function handleNextPage() {
		if (currentPage < totalPages) {
			currentPage++;
			loadCharacters();
		}
	}

	function openAIGenerationModal() {
		// Pre-fill with current filter values
		aiImportance = importance;
		aiUserPrompt = search;
		showAIInputModal = true;
	}

	async function generateWithAI() {
		aiGenerating = true;
		aiError = '';
		aiSuggestions = [];

		try {
			const response = await generateCharacterSuggestions(worldId, {
				importance: aiImportance ?? undefined,
				user_prompt: aiUserPrompt || undefined,
				provider: aiProvider ?? undefined,
				model: aiModel || undefined,
				temperature: aiTemperature ?? undefined
			});

			aiSuggestions = response.suggestions;
			showAIInputModal = false;
			showAIGenerationModal = true;
		} catch (e: any) {
			aiError = e.message || 'Failed to generate characters';
		} finally {
			aiGenerating = false;
		}
	}

	function createCharacterFromSuggestion(suggestion: EntitySuggestion) {
		// Navigate to new character page with pre-filled data
		const params = new URLSearchParams({
			name: suggestion.name,
			description: suggestion.description || '',
			role: suggestion.metadata?.role || '',
			importance: suggestion.metadata?.importance || 'background'
		});
		goto(`/worlds/${worldId}/characters/new?${params}`);
	}

	onMount(() => {
		loadCharacters();
	});
</script>

<svelte:head>
	<title>Characters - SHINKEI</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Breadcrumb -->
	<Breadcrumb
		items={[
			{ label: 'Worlds', href: '/worlds' },
			{ label: 'World', href: `/worlds/${worldId}` },
			{ label: 'Characters', href: `/worlds/${worldId}/characters` }
		]}
	/>

	<!-- Header -->
	<div class="flex items-center justify-between mb-6">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Characters</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				{total} {total === 1 ? 'character' : 'characters'}
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
			<Button href="/worlds/{worldId}/characters/new">Add Character</Button>
		</div>
	</div>

	{#if error}
		<div class="mb-6 rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
			<p class="text-sm text-red-800 dark:text-red-200">{error}</p>
		</div>
	{/if}

	<div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
		<!-- Filters Sidebar -->
		<div class="lg:col-span-1">
			<CharacterFilters bind:importance bind:search onFilterChange={handleFilterChange} />
		</div>

		<!-- Character Grid -->
		<div class="lg:col-span-3">
			{#if loading}
				<div class="flex items-center justify-center py-12">
					<LoadingSpinner />
				</div>
			{:else if characters.length === 0}
				<EmptyState
					title="No characters found"
					description={search || importance
						? 'Try adjusting your filters'
						: 'Get started by creating your first character'}
					actionText={search || importance ? 'Clear Filters' : 'Add Character'}
					actionHref={search || importance ? undefined : `/worlds/${worldId}/characters/new`}
				/>
			{:else}
				<!-- Character Cards Grid -->
				<div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
					{#each characters as character (character.id)}
						<CharacterCard {character} {worldId} />
					{/each}
				</div>

				<!-- Pagination -->
				{#if totalPages > 1}
					<div class="flex items-center justify-between border-t border-gray-200 dark:border-gray-700 pt-4">
						<div class="flex-1 flex justify-between sm:hidden">
							<Button
								variant="secondary"
								size="sm"
								disabled={currentPage === 1}
								on:click={handlePreviousPage}
							>
								Previous
							</Button>
							<Button
								variant="secondary"
								size="sm"
								disabled={currentPage === totalPages}
								on:click={handleNextPage}
							>
								Next
							</Button>
						</div>
						<div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
							<div>
								<p class="text-sm text-gray-700 dark:text-gray-300">
									Showing
									<span class="font-medium">{skip + 1}</span>
									to
									<span class="font-medium">{Math.min(skip + pageSize, total)}</span>
									of
									<span class="font-medium">{total}</span>
									results
								</p>
							</div>
							<div class="flex gap-2">
								<Button
									variant="secondary"
									size="sm"
									disabled={currentPage === 1}
									on:click={handlePreviousPage}
								>
									Previous
								</Button>
								<span class="inline-flex items-center px-3 text-sm text-gray-700 dark:text-gray-300">
									Page {currentPage} of {totalPages}
								</span>
								<Button
									variant="secondary"
									size="sm"
									disabled={currentPage === totalPages}
									on:click={handleNextPage}
								>
									Next
								</Button>
							</div>
						</div>
					</div>
				{/if}
			{/if}
		</div>
	</div>
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
						Generate Characters with AI
					</h2>
					<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
						Configure AI generation settings
					</p>
				</div>

				<!-- Content -->
				<div class="px-6 py-4 space-y-4">
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
							placeholder="Describe the kind of character you want to generate... e.g., 'a mysterious stranger with a dark past'"
							rows="3"
							class="w-full px-3 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
						></textarea>
					</div>

					<!-- Importance -->
					<div>
						<label for="ai-importance" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
							Character Importance
						</label>
						<select
							id="ai-importance"
							bind:value={aiImportance}
							class="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
						>
							<option value={null}>Any importance</option>
							<option value="major">Major</option>
							<option value="minor">Minor</option>
							<option value="background">Background</option>
						</select>
					</div>

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
							Generate Characters
						{/if}
					</Button>
				</div>
			</div>
		</div>
	</div>
{/if}

<!-- AI Generation Modal -->
{#if showAIGenerationModal}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 bg-black/50 z-40 transition-opacity"
		on:click={() => showAIGenerationModal = false}
		on:keydown={(e) => e.key === 'Escape' && (showAIGenerationModal = false)}
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
						AI-Generated Character Suggestions
					</h2>
					<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
						Select a character to create or modify the suggestions
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
							{#each aiSuggestions as suggestion, index}
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
												{#if suggestion.metadata?.importance}
													<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200">
														{suggestion.metadata.importance}
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
													{#if suggestion.metadata.role}
														<p class="text-gray-600 dark:text-gray-400">
															<span class="font-medium">Role:</span> {suggestion.metadata.role}
														</p>
													{/if}
													{#if suggestion.metadata.motivation}
														<p class="text-gray-600 dark:text-gray-400">
															<span class="font-medium">Motivation:</span> {suggestion.metadata.motivation}
														</p>
													{/if}
													{#if suggestion.metadata.personality_traits}
														<p class="text-gray-600 dark:text-gray-400">
															<span class="font-medium">Traits:</span> {suggestion.metadata.personality_traits.join(', ')}
														</p>
													{/if}
												</div>
											{/if}
										</div>

										<Button
											size="sm"
											on:click={() => createCharacterFromSuggestion(suggestion)}
										>
											Create Character
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
						on:click={() => showAIGenerationModal = false}
					>
						Close
					</Button>
					<Button
						variant="secondary"
						on:click={() => {
							showAIGenerationModal = false;
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
