<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type { LocationResponse, LocationUpdate } from '$lib/types/location';
	import { COMMON_LOCATION_TYPES } from '$lib/types/location';
	import Button from '$lib/components/Button.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	const worldId = $page.params.id as string;
	const locationId = $page.params.location_id as string;

	let name = '';
	let description = '';
	let locationType = '';
	let parentLocationId: string | null = null;
	let significance = '';
	let loading = false;
	let loadingLocation = true;
	let error = '';

	// Load all locations for parent selection
	let allLocations: LocationResponse[] = [];

	onMount(async () => {
		try {
			const [locationData, locationsData] = await Promise.all([
				api.get<LocationResponse>(`/worlds/${worldId}/locations/${locationId}`),
				api.get<{ locations: LocationResponse[] }>(
					`/worlds/${worldId}/locations?limit=1000`
				)
			]);

			name = locationData.name;
			description = locationData.description || '';
			locationType = locationData.location_type || '';
			parentLocationId = locationData.parent_location_id || null;
			significance = locationData.significance || '';

			// Filter out current location and its descendants from parent options
			allLocations = locationsData.locations.filter((loc) => loc.id !== locationId);
		} catch (e: any) {
			error = e.message || 'Failed to load location';
		} finally {
			loadingLocation = false;
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
			const locationData: LocationUpdate = {
				name: name.trim(),
				description: description.trim() || undefined,
				location_type: locationType || undefined,
				parent_location_id: parentLocationId || undefined,
				significance: significance.trim() || undefined
			};

			const response = await api.put<LocationResponse>(
				`/worlds/${worldId}/locations/${locationId}`,
				locationData
			);

			addToast({
				type: 'success',
				message: `Location "${response.name}" updated successfully`
			});

			goto(`/worlds/${worldId}/locations/${locationId}`);
		} catch (e: any) {
			error = e.message || 'Failed to update location';
		} finally {
			loading = false;
		}
	}

	function handleCancel() {
		goto(`/worlds/${worldId}/locations/${locationId}`);
	}
</script>

<svelte:head>
	<title>Edit {name || 'Location'} - SHINKEI</title>
</svelte:head>

{#if loadingLocation}
	<div class="flex items-center justify-center min-h-screen">
		<LoadingSpinner size="lg" text="Loading location..." />
	</div>
{:else if error && !name}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<p class="text-red-500 dark:text-red-400 mb-4">{error}</p>
			<a
				href="/worlds/{worldId}/locations"
				class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
			>
				← Back to Locations
			</a>
		</div>
	</div>
{:else}
	<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Breadcrumb -->
		<Breadcrumb
			items={[
				{ label: 'Worlds', href: '/worlds' },
				{ label: 'World', href: `/worlds/${worldId}` },
				{ label: 'Locations', href: `/worlds/${worldId}/locations` },
				{ label: name, href: `/worlds/${worldId}/locations/${locationId}` },
				{ label: 'Edit', href: `/worlds/${worldId}/locations/${locationId}/edit` }
			]}
		/>

		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Edit Location</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				Update location information and metadata
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
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						Optional: Select a parent location to create a hierarchy (e.g., "Diagon Alley" is
						within "London")
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
						<span class="flex items-center gap-2">
							<svg
								class="animate-spin h-4 w-4"
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
							Saving...
						</span>
					{:else}
						Save Changes
					{/if}
				</Button>
			</div>
		</form>
	</div>
{/if}
