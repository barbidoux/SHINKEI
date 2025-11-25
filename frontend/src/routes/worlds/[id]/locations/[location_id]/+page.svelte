<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type { LocationResponse, LocationHierarchyResponse } from '$lib/types/location';
	import { LOCATION_TYPE_COLORS } from '$lib/types/location';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import LocationCard from '$lib/components/LocationCard.svelte';

	const worldId = $page.params.id as string;
	const locationId = $page.params.location_id as string;

	let location: LocationHierarchyResponse | null = null;
	let loading = true;
	let error = '';
	let deleting = false;

	$: typeColor =
		location?.location_type && LOCATION_TYPE_COLORS[location.location_type]
			? LOCATION_TYPE_COLORS[location.location_type]
			: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';

	onMount(async () => {
		try {
			// Get location with hierarchy info
			location = await api.get<LocationHierarchyResponse>(
				`/worlds/${worldId}/locations/${locationId}/hierarchy`
			);
		} catch (e: any) {
			error = e.message || 'Failed to load location';
			console.error('Error loading location:', e);
		} finally {
			loading = false;
		}
	});

	async function handleDelete() {
		if (
			!confirm(
				`Are you sure you want to delete "${location?.name}"? This action cannot be undone.${
					location?.child_locations && location.child_locations.length > 0
						? '\n\nWarning: This location has child locations that will also be affected.'
						: ''
				}`
			)
		) {
			return;
		}

		deleting = true;
		try {
			await api.delete(`/worlds/${worldId}/locations/${locationId}`);

			addToast({
				type: 'success',
				message: `Location "${location?.name}" deleted successfully`
			});

			goto(`/worlds/${worldId}/locations`);
		} catch (e: any) {
			addToast({
				type: 'error',
				message: e.message || 'Failed to delete location'
			});
			deleting = false;
		}
	}

	function formatDate(dateString: string): string {
		return new Date(dateString).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>{location?.name || 'Location'} - SHINKEI</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
				{ label: location.name, href: `/worlds/${worldId}/locations/${locationId}` }
			]}
		/>

		<!-- Header -->
		<div class="border-b border-gray-200 dark:border-gray-700 pb-6 mb-8">
			<div class="flex items-start justify-between mb-3">
				<div class="flex-1">
					<h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
						{location.name}
					</h1>
					<div class="flex items-center gap-3">
						{#if location.location_type}
							<span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium {typeColor}">
								{location.location_type}
							</span>
						{/if}
						{#if location.significance}
							<span
								class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200"
							>
								{location.significance}
							</span>
						{/if}
					</div>
				</div>
				<div class="flex items-center gap-2">
					<a
						href="/worlds/{worldId}/locations/{locationId}/edit"
						class="inline-flex items-center rounded-md bg-white dark:bg-gray-700 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
					>
						✎ Edit
					</a>
					<button
						on:click={handleDelete}
						disabled={deleting}
						class="inline-flex items-center rounded-md bg-red-600 dark:bg-red-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 dark:hover:bg-red-400 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{deleting ? 'Deleting...' : 'Delete'}
					</button>
				</div>
			</div>

			<div class="mt-4">
				<a
					href="/worlds/{worldId}/locations"
					class="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
				>
					← Back to Locations
				</a>
			</div>
		</div>

		<!-- Main Content -->
		<div class="space-y-8">
			<!-- Parent Location -->
			{#if location.parent_location}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
						Parent Location
					</h2>
					<a
						href="/worlds/{worldId}/locations/{location.parent_location.id}"
						class="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-5 w-5"
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
						<span class="font-medium">{location.parent_location.name}</span>
					</a>
				</div>
			{/if}

			<!-- Description -->
			{#if location.description}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Description</h2>
					<p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
						{location.description}
					</p>
				</div>
			{/if}

			<!-- Child Locations -->
			{#if location.child_locations && location.child_locations.length > 0}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
						Child Locations ({location.child_locations.length})
					</h2>
					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						{#each location.child_locations as childLocation}
							<LocationCard location={childLocation} {worldId} showParent={false} />
						{/each}
					</div>
				</div>
			{/if}

			<!-- Coordinates -->
			{#if location.coordinates && Object.keys(location.coordinates).length > 0}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Coordinates</h2>
					<dl class="space-y-2">
						{#each Object.entries(location.coordinates) as [key, value]}
							<div class="flex items-start">
								<dt class="font-medium text-gray-700 dark:text-gray-300 mr-2">{key}:</dt>
								<dd class="text-gray-600 dark:text-gray-400">
									{typeof value === 'object' ? JSON.stringify(value) : value}
								</dd>
							</div>
						{/each}
					</dl>
				</div>
			{/if}

			<!-- Custom Metadata -->
			{#if location.custom_metadata && Object.keys(location.custom_metadata).length > 0}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
						Custom Metadata
					</h2>
					<dl class="space-y-2">
						{#each Object.entries(location.custom_metadata) as [key, value]}
							<div class="flex items-start">
								<dt class="font-medium text-gray-700 dark:text-gray-300 mr-2">{key}:</dt>
								<dd class="text-gray-600 dark:text-gray-400">
									{typeof value === 'object' ? JSON.stringify(value) : value}
								</dd>
							</div>
						{/each}
					</dl>
				</div>
			{/if}

			<!-- Meta Information -->
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
				<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Information</h2>
				<dl class="grid grid-cols-1 sm:grid-cols-2 gap-4">
					<div>
						<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">Created</dt>
						<dd class="mt-1 text-sm text-gray-900 dark:text-white">
							{formatDate(location.created_at)}
						</dd>
					</div>
					<div>
						<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
							Last Updated
						</dt>
						<dd class="mt-1 text-sm text-gray-900 dark:text-white">
							{formatDate(location.updated_at)}
						</dd>
					</div>
					{#if location.first_appearance_beat_id}
						<div>
							<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
								First Appearance
							</dt>
							<dd class="mt-1 text-sm text-gray-900 dark:text-white">
								Beat ID: {location.first_appearance_beat_id}
							</dd>
						</div>
					{/if}
				</dl>
			</div>

			<!-- Quick Actions -->
			<div class="bg-gradient-to-r from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20 rounded-lg p-6 border border-green-200 dark:border-green-800">
				<h2 class="text-lg font-semibold text-green-900 dark:text-green-200 mb-4">
					Quick Actions
				</h2>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<!-- Timeline Link -->
					<a
						href="/worlds/{worldId}/locations/{locationId}/timeline"
						class="flex items-start gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-green-100 dark:border-green-900"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6 text-green-600 dark:text-green-400 flex-shrink-0"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"
							/>
						</svg>
						<div>
							<h3 class="text-sm font-semibold text-gray-900 dark:text-white">View Timeline</h3>
							<p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
								See all story beats that take place at {location.name}
							</p>
						</div>
					</a>

					<!-- Back to Hierarchy -->
					<a
						href="/worlds/{worldId}/locations"
						class="flex items-start gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-teal-100 dark:border-teal-900"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6 text-teal-600 dark:text-teal-400 flex-shrink-0"
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
						<div>
							<h3 class="text-sm font-semibold text-gray-900 dark:text-white">Browse All Locations</h3>
							<p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
								Explore the location hierarchy and map view
							</p>
						</div>
					</a>
				</div>
			</div>
		</div>
	{/if}
</div>
