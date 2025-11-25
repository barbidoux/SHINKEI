<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type { CharacterResponse } from '$lib/types/character';
	import CharacterImportanceBadge from '$lib/components/CharacterImportanceBadge.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';

	const worldId = $page.params.id as string;
	const characterId = $page.params.character_id as string;

	let character: CharacterResponse | null = null;
	let loading = true;
	let error = '';
	let deleting = false;

	onMount(async () => {
		try {
			character = await api.get<CharacterResponse>(
				`/worlds/${worldId}/characters/${characterId}`
			);
		} catch (e: any) {
			error = e.message || 'Failed to load character';
			console.error('Error loading character:', e);
		} finally {
			loading = false;
		}
	});

	async function handleDelete() {
		if (
			!confirm(
				`Are you sure you want to delete "${character?.name}"? This action cannot be undone.`
			)
		) {
			return;
		}

		deleting = true;
		try {
			await api.delete(`/worlds/${worldId}/characters/${characterId}`);

			addToast({
				type: 'success',
				message: `Character "${character?.name}" deleted successfully`
			});

			goto(`/worlds/${worldId}/characters`);
		} catch (e: any) {
			addToast({
				type: 'error',
				message: e.message || 'Failed to delete character'
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
	<title>{character?.name || 'Character'} - SHINKEI</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	{#if loading}
		<div class="flex items-center justify-center py-12">
			<LoadingSpinner size="lg" text="Loading character..." />
		</div>
	{:else if error}
		<div class="text-center py-12">
			<p class="text-red-500 dark:text-red-400 mb-4">{error}</p>
			<a
				href="/worlds/{worldId}/characters"
				class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
			>
				← Back to Characters
			</a>
		</div>
	{:else if character}
		<!-- Breadcrumb -->
		<Breadcrumb
			items={[
				{ label: 'Worlds', href: '/worlds' },
				{ label: 'World', href: `/worlds/${worldId}` },
				{ label: 'Characters', href: `/worlds/${worldId}/characters` },
				{ label: character.name, href: `/worlds/${worldId}/characters/${characterId}` }
			]}
		/>

		<!-- Header -->
		<div class="border-b border-gray-200 dark:border-gray-700 pb-6 mb-8">
			<div class="flex items-start justify-between mb-3">
				<div class="flex-1">
					<h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-2">
						{character.name}
					</h1>
					<div class="flex items-center gap-3">
						<CharacterImportanceBadge importance={character.importance} size="md" />
						{#if character.role}
							<span
								class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 dark:bg-purple-900 text-purple-800 dark:text-purple-200"
							>
								{character.role}
							</span>
						{/if}
					</div>
				</div>
				<div class="flex items-center gap-2">
					<a
						href="/worlds/{worldId}/characters/{characterId}/edit"
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
					href="/worlds/{worldId}/characters"
					class="text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
				>
					← Back to Characters
				</a>
			</div>
		</div>

		<!-- Main Content -->
		<div class="space-y-8">
			<!-- Aliases -->
			{#if character.aliases && character.aliases.length > 0}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Aliases</h2>
					<div class="flex flex-wrap gap-2">
						{#each character.aliases as alias}
							<span
								class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
							>
								{alias}
							</span>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Description -->
			{#if character.description}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">Description</h2>
					<p class="text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
						{character.description}
					</p>
				</div>
			{/if}

			<!-- Custom Metadata -->
			{#if character.custom_metadata && Object.keys(character.custom_metadata).length > 0}
				<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
					<h2 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
						Custom Metadata
					</h2>
					<dl class="space-y-2">
						{#each Object.entries(character.custom_metadata) as [key, value]}
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
							{formatDate(character.created_at)}
						</dd>
					</div>
					<div>
						<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
							Last Updated
						</dt>
						<dd class="mt-1 text-sm text-gray-900 dark:text-white">
							{formatDate(character.updated_at)}
						</dd>
					</div>
					{#if character.first_appearance_beat_id}
						<div>
							<dt class="text-sm font-medium text-gray-500 dark:text-gray-400">
								First Appearance
							</dt>
							<dd class="mt-1 text-sm text-gray-900 dark:text-white">
								Beat ID: {character.first_appearance_beat_id}
							</dd>
						</div>
					{/if}
				</dl>
			</div>

			<!-- Quick Actions -->
			<div class="bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg p-6 border border-indigo-200 dark:border-indigo-800">
				<h2 class="text-lg font-semibold text-indigo-900 dark:text-indigo-200 mb-4">
					Quick Actions
				</h2>
				<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
					<!-- Timeline Link -->
					<a
						href="/worlds/{worldId}/characters/{characterId}/timeline"
						class="flex items-start gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-indigo-100 dark:border-indigo-900"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6 text-indigo-600 dark:text-indigo-400 flex-shrink-0"
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
								See all story beats where {character.name} appears
							</p>
						</div>
					</a>

					<!-- Relationships Link -->
					<a
						href="/worlds/{worldId}/relationships?character={characterId}"
						class="flex items-start gap-3 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-purple-100 dark:border-purple-900"
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							class="h-6 w-6 text-purple-600 dark:text-purple-400 flex-shrink-0"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
							/>
						</svg>
						<div>
							<h3 class="text-sm font-semibold text-gray-900 dark:text-white">View Relationships</h3>
							<p class="text-xs text-gray-600 dark:text-gray-400 mt-1">
								Explore {character.name}'s connections with other characters
							</p>
						</div>
					</a>
				</div>
			</div>
		</div>
	{/if}
</div>
