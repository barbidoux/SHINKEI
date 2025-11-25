<script lang="ts">
	import type { LocationTreeNode } from '$lib/types/location';
	import { LOCATION_TYPE_COLORS } from '$lib/types/location';

	export let node: LocationTreeNode;
	export let worldId: string;

	let expanded = true;

	function toggleExpanded() {
		expanded = !expanded;
	}

	function getTypeColor(locationType: string | undefined): string {
		if (!locationType || !LOCATION_TYPE_COLORS[locationType]) {
			return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
		}
		return LOCATION_TYPE_COLORS[locationType];
	}

	$: hasChildren = node.children && node.children.length > 0;
	$: indentClass = `pl-${Math.min(node.level * 4, 16)}`;
	$: typeColor = getTypeColor(node.location_type);
</script>

<div class="location-tree-node">
	<!-- Node Content -->
	<div
		class="flex items-center gap-2 py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors {indentClass}"
	>
		<!-- Expand/Collapse Button -->
		{#if hasChildren}
			<button
				type="button"
				on:click={toggleExpanded}
				class="flex-shrink-0 w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
				aria-label={expanded ? 'Collapse' : 'Expand'}
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4 transition-transform {expanded ? 'rotate-90' : ''}"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
				</svg>
			</button>
		{:else}
			<div class="w-5 h-5 flex-shrink-0"></div>
		{/if}

		<!-- Location Icon -->
		<svg
			xmlns="http://www.w3.org/2000/svg"
			class="h-5 w-5 text-gray-400 flex-shrink-0"
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
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
		</svg>

		<!-- Location Name (Link) -->
		<a
			href="/worlds/{worldId}/locations/{node.id}"
			class="text-sm font-medium text-gray-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 flex-1 truncate"
		>
			{node.name}
		</a>

		<!-- Location Type Badge -->
		{#if node.location_type}
			<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium {typeColor}">
				{node.location_type}
			</span>
		{/if}

		<!-- Child Count -->
		{#if hasChildren}
			<span class="text-xs text-gray-500 dark:text-gray-400 flex-shrink-0">
				{node.children.length} {node.children.length === 1 ? 'child' : 'children'}
			</span>
		{/if}
	</div>

	<!-- Children (Recursively rendered) -->
	{#if hasChildren && expanded}
		<div class="ml-2 border-l-2 border-gray-200 dark:border-gray-700">
			{#each node.children as childNode}
				<svelte:self node={childNode} {worldId} />
			{/each}
		</div>
	{/if}
</div>
