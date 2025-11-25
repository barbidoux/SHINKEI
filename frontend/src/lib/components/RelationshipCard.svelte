<script lang="ts">
	import type { CharacterRelationshipResponse } from '$lib/types/relationship';
	import { RELATIONSHIP_STRENGTH_COLORS } from '$lib/types/relationship';

	export let relationship: CharacterRelationshipResponse;
	export let worldId: string;
	export let characterAName: string = '';
	export let characterBName: string = '';

	$: strengthColor = RELATIONSHIP_STRENGTH_COLORS[relationship.strength] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';

	function truncate(text: string, maxLength: number): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
</script>

<a
	href="/worlds/{worldId}/relationships/{relationship.id}/edit"
	class="block bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700 p-4"
>
	<!-- Header with relationship direction -->
	<div class="flex items-center justify-between mb-3">
		<div class="flex items-center gap-2 flex-1 min-w-0">
			<span class="text-sm font-medium text-gray-900 dark:text-white truncate">
				{characterAName}
			</span>
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-4 w-4 flex-shrink-0 text-gray-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				{#if relationship.is_mutual}
					<!-- Bidirectional arrow -->
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
					/>
				{:else}
					<!-- Unidirectional arrow -->
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M14 5l7 7m0 0l-7 7m7-7H3"
					/>
				{/if}
			</svg>
			<span class="text-sm font-medium text-gray-900 dark:text-white truncate">
				{characterBName}
			</span>
		</div>
		<span
			class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {strengthColor} flex-shrink-0 ml-2"
		>
			{relationship.strength}
		</span>
	</div>

	<!-- Relationship Type -->
	<div class="mb-2">
		<span
			class="inline-flex items-center px-2 py-1 rounded-md text-sm font-medium bg-indigo-100 dark:bg-indigo-900 text-indigo-800 dark:text-indigo-200"
		>
			{relationship.relationship_type}
		</span>
	</div>

	<!-- Description -->
	{#if relationship.description}
		<p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
			{truncate(relationship.description, 120)}
		</p>
	{/if}

	<!-- Meta Information -->
	<div class="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-700 pt-3">
		{#if relationship.is_mutual}
			<span class="flex items-center gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3 w-3"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
					/>
				</svg>
				Mutual
			</span>
		{:else}
			<span class="flex items-center gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3 w-3"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M14 5l7 7m0 0l-7 7m7-7H3"
					/>
				</svg>
				One-way
			</span>
		{/if}
		{#if relationship.first_established_beat_id}
			<span class="flex items-center gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-3 w-3"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 6v6m0 0v6m0-6h6m-6 0H6"
					/>
				</svg>
				Has origin beat
			</span>
		{/if}
	</div>
</a>
