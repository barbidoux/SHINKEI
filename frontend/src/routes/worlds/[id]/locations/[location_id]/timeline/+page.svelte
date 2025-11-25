<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { browser } from '$app/environment';
	import { api } from '$lib/api';
	import type { LocationResponse } from '$lib/types/location';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import Button from '$lib/components/Button.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import EntityTimeline from '$lib/components/EntityTimeline.svelte';

	const worldId = $page.params.id as string;
	const locationId = $page.params.location_id as string;

	let location: LocationResponse | null = null;
	let loading = true;
	let error = '';

	let apiUrl: string;
	$: apiUrl = browser ? import.meta.env.VITE_API_URL || '' : '';

	onMount(async () => {
		try {
			location = await api.get<LocationResponse>(
				`/worlds/${worldId}/locations/${locationId}`
			);
		} catch (e: any) {
			error = e.message || 'Failed to load location';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>{location?.name || 'Location'} Timeline - SHINKEI</title>
</svelte:head>

<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" text="Loading location..." />
		</div>
	{:else if error}
		<div class="text-center py-12">
			<p class="text-red-500 dark:text-red-400 mb-4">{error}</p>
			<a
				href="/worlds/{worldId}/locations"
				class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
			>
				← Back to Locations
			</a>
		</div>
	{:else if location}
		<!-- Breadcrumb -->
		<Breadcrumb
			items={[
				{ label: 'Worlds', href: '/worlds' },
				{ label: 'World', href: `/worlds/${worldId}` },
				{ label: 'Locations', href: `/worlds/${worldId}/locations` },
				{ label: location.name, href: `/worlds/${worldId}/locations/${locationId}` },
				{ label: 'Timeline', href: `/worlds/${worldId}/locations/${locationId}/timeline` }
			]}
		/>

		<!-- Header -->
		<div class="flex items-center justify-between mb-8">
			<div>
				<h1 class="text-3xl font-bold text-gray-900 dark:text-white">
					{location.name} Timeline
				</h1>
				<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
					Track where this location appears across all story beats
				</p>
			</div>
			<Button href="/worlds/{worldId}/locations/{locationId}" variant="secondary">
				← Back to Location
			</Button>
		</div>

		<!-- Timeline Component -->
		<EntityTimeline
			entityId={locationId}
			entityType="location"
			entityName={location.name}
			{apiUrl}
		/>

		<!-- Info Box -->
		<div class="mt-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 border border-blue-200 dark:border-blue-800">
			<h3 class="text-sm font-semibold text-blue-900 dark:text-blue-200 mb-2">
				About Entity Timelines
			</h3>
			<p class="text-sm text-blue-700 dark:text-blue-300 mb-2">
				This timeline shows all story beats where <strong>{location.name}</strong> is mentioned.
				Each box represents a mention in a story beat.
			</p>
			<ul class="text-sm text-blue-700 dark:text-blue-300 space-y-1 list-disc list-inside">
				<li><strong>Rows</strong> represent different stories</li>
				<li><strong>Green boxes</strong> are explicit mentions (location directly appears)</li>
				<li><strong>Yellow boxes</strong> are implicit mentions (location is involved)</li>
				<li><strong>Gray boxes</strong> are referenced mentions (location is mentioned)</li>
				<li><strong>Click a box</strong> to navigate to that story beat</li>
			</ul>
		</div>
	{/if}
</div>
