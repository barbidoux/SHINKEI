<script lang="ts">
	import type { LocationResponse } from '$lib/types/location';
	import { LOCATION_TYPE_COLORS } from '$lib/types/location';

	export let location: LocationResponse;
	export let worldId: string;
	export let showParent: boolean = false;
	export let parentLocation: LocationResponse | undefined = undefined;

	$: typeColor =
		location.location_type && LOCATION_TYPE_COLORS[location.location_type]
			? LOCATION_TYPE_COLORS[location.location_type]
			: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';

	function truncate(text: string, maxLength: number): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}
</script>

<a
	href="/worlds/{worldId}/locations/{location.id}"
	class="block bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700 p-4"
>
	<!-- Header -->
	<div class="flex items-start justify-between mb-2">
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate flex-1">
			{location.name}
		</h3>
		{#if location.location_type}
			<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {typeColor}">
				{location.location_type}
			</span>
		{/if}
	</div>

	<!-- Parent Location -->
	{#if showParent && parentLocation}
		<div class="mb-2">
			<span class="text-xs text-gray-500 dark:text-gray-400">
				in <span class="font-medium">{parentLocation.name}</span>
			</span>
		</div>
	{/if}

	<!-- Description -->
	{#if location.description}
		<p class="text-sm text-gray-600 dark:text-gray-400 mb-3">
			{truncate(location.description, 150)}
		</p>
	{/if}

	<!-- Meta Information -->
	<div class="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400 border-t border-gray-100 dark:border-gray-700 pt-3">
		{#if location.significance}
			<span class="flex items-center gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
					/>
				</svg>
				{location.significance}
			</span>
		{/if}
		{#if location.coordinates}
			<span class="flex items-center gap-1">
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4"
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
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
					/>
				</svg>
				Coordinates
			</span>
		{/if}
	</div>
</a>
