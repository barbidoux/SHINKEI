<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { CharacterResponse } from '$lib/types/character';
	import type { LocationResponse } from '$lib/types/location';
	import { extractEntitiesFromBeat } from '$lib/api/entity-generation';

	const dispatch = createEventDispatcher();

	export let worldId: string;
	export let storyId: string;
	export let beatId: string;
	export let beatContent: string;
	export let detecting: boolean = false;

	interface EntitySuggestion {
		entity_type: 'character' | 'location';
		entity_id?: string; // If already exists
		entity_name: string;
		confidence: number;
		context_snippet?: string;
		mention_type?: 'explicit' | 'implicit' | 'referenced';
		description?: string;
		metadata?: Record<string, any>;
	}

	let suggestions: EntitySuggestion[] = [];
	let loading = false;
	let error = '';
	let acceptedIds = new Set<number>();
	let rejectedIds = new Set<number>();

	export async function detectEntities() {
		loading = true;
		error = '';
		suggestions = [];
		acceptedIds.clear();
		rejectedIds.clear();

		try {
			// Call the real AI API endpoint
			const response = await extractEntitiesFromBeat(worldId, storyId, beatId, {
				text: beatContent,
				confidence_threshold: 0.7
			});

			// Map API response to component format
			suggestions = response.suggestions.map((s) => ({
				entity_type: s.entity_type,
				entity_name: s.name,
				confidence: s.confidence,
				context_snippet: s.context_snippet || '',
				mention_type: 'explicit', // Default, could be inferred from metadata
				description: s.description,
				metadata: s.metadata
			}));

			dispatch('detectionComplete', { suggestions });
		} catch (e: any) {
			error = e.message || 'Failed to detect entities';
		} finally {
			loading = false;
		}
	}

	function getConfidenceIcon(confidence: number): string {
		if (confidence >= 0.9) return '✓';
		if (confidence >= 0.7) return '⚠️';
		return '?';
	}

	function getConfidenceColor(confidence: number): string {
		if (confidence >= 0.9) return 'text-green-600 dark:text-green-400';
		if (confidence >= 0.7) return 'text-yellow-600 dark:text-yellow-400';
		return 'text-gray-600 dark:text-gray-400';
	}

	function getConfidenceBgColor(confidence: number): string {
		if (confidence >= 0.9) return 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800';
		if (confidence >= 0.7) return 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800';
		return 'bg-gray-50 dark:bg-gray-900/20 border-gray-200 dark:border-gray-700';
	}

	function acceptSuggestion(index: number) {
		acceptedIds.add(index);
		rejectedIds.delete(index);
		acceptedIds = acceptedIds; // Trigger reactivity
	}

	function rejectSuggestion(index: number) {
		rejectedIds.add(index);
		acceptedIds.delete(index);
		rejectedIds = rejectedIds; // Trigger reactivity
	}

	function acceptAll() {
		suggestions.forEach((_, index) => {
			acceptedIds.add(index);
		});
		rejectedIds.clear();
		acceptedIds = acceptedIds;
	}

	function rejectAll() {
		acceptedIds.clear();
		suggestions.forEach((_, index) => {
			rejectedIds.add(index);
		});
		rejectedIds = rejectedIds;
	}

	function applyAccepted() {
		const accepted = suggestions.filter((_, index) => acceptedIds.has(index));
		dispatch('apply', { suggestions: accepted });
	}

	$: hasAccepted = acceptedIds.size > 0;
</script>

<div class="entity-suggestions-panel">
	{#if loading}
		<div class="text-center py-8">
			<svg
				class="animate-spin h-8 w-8 mx-auto mb-3 text-indigo-600"
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
			<p class="text-sm text-gray-600 dark:text-gray-400">
				Detecting entities with AI...
			</p>
		</div>
	{:else if error}
		<div class="text-center py-8 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
			<p class="text-sm text-red-600 dark:text-red-400">{error}</p>
		</div>
	{:else if suggestions.length > 0}
		<!-- Suggestions Header -->
		<div class="flex items-center justify-between mb-4">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
				AI Detected {suggestions.length} Entit{suggestions.length === 1 ? 'y' : 'ies'}
			</h3>
			<div class="flex items-center gap-2">
				<button
					type="button"
					on:click={acceptAll}
					class="text-sm text-green-600 dark:text-green-400 hover:text-green-700 dark:hover:text-green-300 font-medium"
				>
					Accept All
				</button>
				<span class="text-gray-300 dark:text-gray-600">|</span>
				<button
					type="button"
					on:click={rejectAll}
					class="text-sm text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 font-medium"
				>
					Reject All
				</button>
			</div>
		</div>

		<!-- Suggestions List -->
		<div class="space-y-3 mb-4">
			{#each suggestions as suggestion, index}
				{@const isAccepted = acceptedIds.has(index)}
				{@const isRejected = rejectedIds.has(index)}
				<div
					class="p-4 rounded-lg border-2 transition-all {getConfidenceBgColor(
						suggestion.confidence
					)} {isAccepted
						? 'ring-2 ring-green-500 dark:ring-green-400'
						: isRejected
						  ? 'opacity-50'
						  : ''}"
				>
					<div class="flex items-start justify-between mb-2">
						<div class="flex items-center gap-2 flex-1">
							<span
								class="text-2xl {getConfidenceColor(suggestion.confidence)}"
								title={`${Math.round(suggestion.confidence * 100)}% confidence`}
							>
								{getConfidenceIcon(suggestion.confidence)}
							</span>
							<div>
								<div class="flex items-center gap-2">
									<span class="font-semibold text-gray-900 dark:text-white">
										{suggestion.entity_name}
									</span>
									<span
										class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium {suggestion.entity_type ===
										'character'
											? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
											: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'}"
									>
										{suggestion.entity_type}
									</span>
									<span
										class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
									>
										{Math.round(suggestion.confidence * 100)}%
									</span>
								</div>
								<p class="text-sm text-gray-600 dark:text-gray-400 mt-1">
									{suggestion.mention_type} mention
								</p>
							</div>
						</div>
						<div class="flex items-center gap-2 ml-2">
							{#if !isAccepted && !isRejected}
								<button
									type="button"
									on:click={() => acceptSuggestion(index)}
									class="px-3 py-1 text-sm font-medium text-green-700 dark:text-green-300 bg-green-100 dark:bg-green-900/50 rounded hover:bg-green-200 dark:hover:bg-green-900"
								>
									Accept
								</button>
								<button
									type="button"
									on:click={() => rejectSuggestion(index)}
									class="px-3 py-1 text-sm font-medium text-red-700 dark:text-red-300 bg-red-100 dark:bg-red-900/50 rounded hover:bg-red-200 dark:hover:bg-red-900"
								>
									Reject
								</button>
							{:else if isAccepted}
								<span class="text-sm font-medium text-green-600 dark:text-green-400">
									✓ Accepted
								</span>
								<button
									type="button"
									on:click={() => rejectSuggestion(index)}
									class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
								>
									Undo
								</button>
							{:else}
								<span class="text-sm font-medium text-red-600 dark:text-red-400">
									✗ Rejected
								</span>
								<button
									type="button"
									on:click={() => acceptSuggestion(index)}
									class="text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
								>
									Undo
								</button>
							{/if}
						</div>
					</div>

					<!-- Context Snippet -->
					<div class="mt-2 p-2 bg-white dark:bg-gray-800 rounded text-sm">
						<p class="text-gray-700 dark:text-gray-300 italic">
							"{suggestion.context_snippet}"
						</p>
					</div>
				</div>
			{/each}
		</div>

		<!-- Apply Button -->
		{#if hasAccepted}
			<div class="flex items-center justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
				<button
					type="button"
					on:click={applyAccepted}
					class="inline-flex items-center px-4 py-2 rounded-md bg-indigo-600 text-white font-semibold hover:bg-indigo-500 shadow-sm"
				>
					Apply {acceptedIds.size} Accepted Suggestion{acceptedIds.size === 1 ? '' : 's'}
				</button>
			</div>
		{/if}
	{:else}
		<div class="text-center py-8 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-12 w-12 mx-auto text-gray-400 mb-3"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
				/>
			</svg>
			<p class="text-sm text-gray-600 dark:text-gray-400">
				Click "Detect Entities" to find characters and locations in this beat using AI
			</p>
		</div>
	{/if}
</div>

<style>
	.entity-suggestions-panel {
		width: 100%;
	}
</style>
