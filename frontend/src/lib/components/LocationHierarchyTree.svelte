<script lang="ts">
	import type { LocationTreeNode, LocationResponse } from '$lib/types/location';
	import { buildLocationTree, LOCATION_TYPE_COLORS } from '$lib/types/location';
	import LocationTreeNodeComponent from './LocationTreeNodeComponent.svelte';

	export let locations: LocationResponse[];
	export let worldId: string;

	$: tree = buildLocationTree(locations);
</script>

<div class="space-y-2">
	{#if tree.length === 0}
		<p class="text-sm text-gray-500 dark:text-gray-400 italic">No locations found</p>
	{:else}
		{#each tree as node}
			<LocationTreeNodeComponent {node} {worldId} />
		{/each}
	{/if}
</div>
