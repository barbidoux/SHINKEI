<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type { LocationCreate, LocationResponse } from '$lib/types/location';
	import { COMMON_LOCATION_TYPES } from '$lib/types/location';
	import Button from '$lib/components/Button.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';

	const worldId = $page.params.id as string;

	let name = '';
	let description = '';
	let locationType = '';
	let parentLocationId: string | null = null;
	let significance = '';
	let loading = false;
	let error = '';

	// Load all locations for parent selection
	let allLocations: LocationResponse[] = [];
	let loadingLocations = true;

	onMount(async () => {
		try {
			const response = await api.get<{ locations: LocationResponse[] }>(
				`/worlds/${worldId}/locations?limit=1000`
			);
			allLocations = response.locations;
		} catch (e: any) {
			console.error('Error loading locations for parent selection:', e);
		} finally {
			loadingLocations = false;
		}
	});

	async function handleSubmit() {
		if (!name.trim()) {
			error = 'Location name is required';
			return;
		}

		loading = true;
		error = '';

		try {
			const locationData: LocationCreate = {
				name: name.trim(),
				description: description.trim() || undefined,
				location_type: locationType || undefined,
				parent_location_id: parentLocationId || undefined,
				significance: significance.trim() || undefined
			};

			const response = await api.post<LocationResponse>(
				`/worlds/${worldId}/locations`,
				locationData
			);

			addToast({
				type: 'success',
				message: `Location "${response.name}" created successfully`
			});

			goto(`/worlds/${worldId}/locations/${response.id}`);
		} catch (e: any) {
			error = e.message || 'Failed to create location';
			console.error('Error creating location:', e);
		} finally {
			loading = false;
		}
	}

	function handleCancel() {
		goto(`/worlds/${worldId}/locations`);
	}
</script>

<svelte:head>
	<title>New Location - SHINKEI</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Breadcrumb -->
	<Breadcrumb
		items={[
			{ label: 'Worlds', href: '/worlds' },
			{ label: 'World', href: `/worlds/${worldId}` },
			{ label: 'Locations', href: `/worlds/${worldId}/locations` },
			{ label: 'New', href: `/worlds/${worldId}/locations/new` }
		]}
	/>

	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Create New Location</h1>
		<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
			Add a new place, building, or area to your world
		</p>
	</div>

	<!-- Form -->
	<form on:submit|preventDefault={handleSubmit} class="space-y-6">
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
			<!-- Name (Required) -->
			<div>
				<label for="name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Name <span class="text-red-500">*</span>
				</label>
				<input
					type="text"
					id="name"
					bind:value={name}
					required
					placeholder="e.g., Rivendell, Hogwarts Castle, Coruscant"
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				/>
			</div>

			<!-- Location Type -->
			<div>
				<label
					for="location_type"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
				>
					Location Type
				</label>
				<input
					type="text"
					id="location_type"
					bind:value={locationType}
					list="common-location-types"
					placeholder="e.g., city, building, planet, forest"
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				/>
				<datalist id="common-location-types">
					{#each COMMON_LOCATION_TYPES as type}
						<option value={type} />
					{/each}
				</datalist>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					The type or category of this location
				</p>
			</div>

			<!-- Parent Location -->
			<div>
				<label
					for="parent_location"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
				>
					Parent Location
				</label>
				{#if loadingLocations}
					<p class="text-sm text-gray-500 dark:text-gray-400">Loading locations...</p>
				{:else}
					<select
						id="parent_location"
						bind:value={parentLocationId}
						class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
					>
						<option value={null}>None (Top-level location)</option>
						{#each allLocations as location}
							<option value={location.id}>{location.name}</option>
						{/each}
					</select>
				{/if}
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					Optional: Select a parent location to create a hierarchy (e.g., "Diagon Alley" is within
					"London")
				</p>
			</div>

			<!-- Significance -->
			<div>
				<label
					for="significance"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
				>
					Significance
				</label>
				<input
					type="text"
					id="significance"
					bind:value={significance}
					placeholder="e.g., major, minor, background"
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				/>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					How important this location is to the story
				</p>
			</div>

			<!-- Description -->
			<div>
				<label
					for="description"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
				>
					Description
				</label>
				<textarea
					id="description"
					bind:value={description}
					rows="6"
					placeholder="Describe the location's appearance, atmosphere, history, and notable features..."
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				/>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					Detailed description of the location
				</p>
			</div>
		</div>

		<!-- Error Message -->
		{#if error}
			<div class="rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
				<p class="text-sm text-red-800 dark:text-red-200">{error}</p>
			</div>
		{/if}

		<!-- Actions -->
		<div class="flex items-center justify-between pt-4">
			<Button type="button" variant="secondary" on:click={handleCancel} disabled={loading}>
				Cancel
			</Button>
			<Button type="submit" disabled={loading}>
				{#if loading}
					Creating...
				{:else}
					Create Location
				{/if}
			</Button>
		</div>
	</form>
</div>
