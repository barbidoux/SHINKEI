<script lang="ts">
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import Button from '$lib/components/Button.svelte';
	import CharacterRelationshipGraph from '$lib/components/CharacterRelationshipGraph.svelte';

	const worldId = $page.params.id as string;

	// Get API URL from environment or default
	let apiUrl: string;
	$: apiUrl = browser ? import.meta.env.VITE_API_URL || '' : '';
</script>

<svelte:head>
	<title>Relationship Network Graph - SHINKEI</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Breadcrumb -->
	<Breadcrumb
		items={[
			{ label: 'Worlds', href: '/worlds' },
			{ label: 'World', href: `/worlds/${worldId}` },
			{ label: 'Relationships', href: `/worlds/${worldId}/relationships` },
			{ label: 'Graph', href: `/worlds/${worldId}/relationships/graph` }
		]}
	/>

	<!-- Header -->
	<div class="flex items-center justify-between mb-8">
		<div>
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">
				Character Relationship Network
			</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				Visual network graph of character relationships
			</p>
		</div>
		<Button href="/worlds/{worldId}/relationships" variant="secondary">
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
					d="M4 6h16M4 10h16M4 14h16M4 18h16"
				/>
			</svg>
			View List
		</Button>
	</div>

	<!-- Graph Component -->
	<CharacterRelationshipGraph {worldId} {apiUrl} />

	<!-- Help Text -->
	<div class="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
		<h3 class="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
			Interacting with the Graph
		</h3>
		<ul class="text-sm text-blue-700 dark:text-blue-300 space-y-1 list-disc list-inside">
			<li><strong>Drag nodes</strong> to rearrange the network</li>
			<li><strong>Scroll to zoom</strong> in and out</li>
			<li><strong>Pan by dragging</strong> the background</li>
			<li>
				<strong>Node size</strong> represents character importance (larger = more important)
			</li>
			<li><strong>Edge thickness</strong> represents relationship strength</li>
			<li><strong>Hover over nodes</strong> to see character details</li>
			<li><strong>Edge labels</strong> show the relationship type</li>
		</ul>
	</div>
</div>
