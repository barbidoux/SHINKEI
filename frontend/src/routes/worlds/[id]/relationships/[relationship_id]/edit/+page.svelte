<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type {
		CharacterRelationshipResponse,
		CharacterRelationshipUpdate,
		RelationshipStrength
	} from '$lib/types/relationship';
	import type { Character } from '$lib/types/character';
	import {
		RELATIONSHIP_STRENGTH_OPTIONS,
		COMMON_RELATIONSHIP_TYPES
	} from '$lib/types/relationship';
	import Button from '$lib/components/Button.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	const worldId = $page.params.id as string;
	const relationshipId = $page.params.relationship_id as string;

	let relationship: CharacterRelationshipResponse | null = null;
	let characterAName = '';
	let characterBName = '';

	let relationshipType = '';
	let description = '';
	let strength: RelationshipStrength = 'moderate';
	let isMutual = true;

	let loading = false;
	let loadingRelationship = true;
	let error = '';
	let deleting = false;

	onMount(async () => {
		try {
			relationship = await api.get<CharacterRelationshipResponse>(
				`/worlds/${worldId}/character-relationships/${relationshipId}`
			);

			relationshipType = relationship.relationship_type;
			description = relationship.description || '';
			strength = relationship.strength;
			isMutual = relationship.is_mutual;

			// Load character names
			const [charA, charB] = await Promise.all([
				api.get<Character>(`/worlds/${worldId}/characters/${relationship.character_a_id}`),
				api.get<Character>(`/worlds/${worldId}/characters/${relationship.character_b_id}`)
			]);

			characterAName = charA.name;
			characterBName = charB.name;
		} catch (e: any) {
			error = e.message || 'Failed to load relationship';
		} finally {
			loadingRelationship = false;
		}
	});

	async function handleSubmit() {
		if (!relationshipType.trim()) {
			error = 'Relationship type is required';
			return;
		}

		loading = true;
		error = '';

		try {
			const relationshipData: CharacterRelationshipUpdate = {
				relationship_type: relationshipType.trim(),
				description: description.trim() || undefined,
				strength,
				is_mutual: isMutual
			};

			await api.put<CharacterRelationshipResponse>(
				`/worlds/${worldId}/character-relationships/${relationshipId}`,
				relationshipData
			);

			addToast({
				type: 'success',
				message: 'Relationship updated successfully'
			});

			goto(`/worlds/${worldId}/relationships`);
		} catch (e: any) {
			error = e.message || 'Failed to update relationship';
		} finally {
			loading = false;
		}
	}

	async function handleDelete() {
		if (!confirm('Are you sure you want to delete this relationship? This action cannot be undone.')) {
			return;
		}

		deleting = true;
		try {
			await api.delete(`/worlds/${worldId}/character-relationships/${relationshipId}`);

			addToast({
				type: 'success',
				message: 'Relationship deleted successfully'
			});

			goto(`/worlds/${worldId}/relationships`);
		} catch (e: any) {
			addToast({
				type: 'error',
				message: e.message || 'Failed to delete relationship'
			});
			deleting = false;
		}
	}

	function handleCancel() {
		goto(`/worlds/${worldId}/relationships`);
	}
</script>

<svelte:head>
	<title>Edit Relationship - SHINKEI</title>
</svelte:head>

{#if loadingRelationship}
	<div class="flex items-center justify-center min-h-screen">
		<LoadingSpinner size="lg" text="Loading relationship..." />
	</div>
{:else if error && !relationship}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<p class="text-red-500 dark:text-red-400 mb-4">{error}</p>
			<a
				href="/worlds/{worldId}/relationships"
				class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
			>
				← Back to Relationships
			</a>
		</div>
	</div>
{:else if relationship}
	<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
		<!-- Breadcrumb -->
		<Breadcrumb
			items={[
				{ label: 'Worlds', href: '/worlds' },
				{ label: 'World', href: `/worlds/${worldId}` },
				{ label: 'Relationships', href: `/worlds/${worldId}/relationships` },
				{ label: 'Edit', href: `/worlds/${worldId}/relationships/${relationshipId}/edit` }
			]}
		/>

		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Edit Relationship</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				{characterAName} ↔ {characterBName}
			</p>
		</div>

		<!-- Form -->
		<form on:submit|preventDefault={handleSubmit} class="space-y-6">
			<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
				<!-- Character Display (Read-only) -->
				<div class="bg-gray-50 dark:bg-gray-900/50 rounded-md p-4 border border-gray-200 dark:border-gray-700">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-3">
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{characterAName}
							</span>
							<svg
								xmlns="http://www.w3.org/2000/svg"
								class="h-5 w-5 text-gray-400"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								{#if isMutual}
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"
									/>
								{:else}
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M14 5l7 7m0 0l-7 7m7-7H3"
									/>
								{/if}
							</svg>
							<span class="text-sm font-medium text-gray-900 dark:text-white">
								{characterBName}
							</span>
						</div>
						<span class="text-xs text-gray-500 dark:text-gray-400">
							Characters cannot be changed
						</span>
					</div>
				</div>

				<!-- Relationship Type -->
				<div>
					<label
						for="relationship_type"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
					>
						Relationship Type <span class="text-red-500">*</span>
					</label>
					<input
						type="text"
						id="relationship_type"
						bind:value={relationshipType}
						required
						list="common-relationship-types"
						placeholder="e.g., friendship, romantic, rivalry"
						class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
					/>
					<datalist id="common-relationship-types">
						{#each COMMON_RELATIONSHIP_TYPES as type}
							<option value={type} />
						{/each}
					</datalist>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						The nature of their connection
					</p>
				</div>

				<!-- Strength -->
				<div>
					<label
						for="strength"
						class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
					>
						Strength
					</label>
					<select
						id="strength"
						bind:value={strength}
						class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
					>
						{#each RELATIONSHIP_STRENGTH_OPTIONS as option}
							<option value={option.value}>{option.label}</option>
						{/each}
					</select>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						How strong or significant this relationship is
					</p>
				</div>

				<!-- Is Mutual -->
				<div>
					<label class="flex items-center gap-2">
						<input
							type="checkbox"
							bind:checked={isMutual}
							class="rounded border-gray-300 dark:border-gray-600 text-indigo-600 focus:ring-indigo-500"
						/>
						<span class="text-sm font-medium text-gray-700 dark:text-gray-300">
							Mutual Relationship
						</span>
					</label>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400 ml-6">
						Check if this relationship goes both ways
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
						rows="4"
						placeholder="Describe the dynamics of this relationship..."
						class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
					/>
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						Optional details about how these characters relate to each other
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
				<div class="flex items-center gap-2">
					<Button type="button" variant="secondary" on:click={handleCancel} disabled={loading || deleting}>
						Cancel
					</Button>
					<button
						type="button"
						on:click={handleDelete}
						disabled={loading || deleting}
						class="inline-flex items-center rounded-md bg-red-600 dark:bg-red-500 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-500 dark:hover:bg-red-400 disabled:opacity-50 disabled:cursor-not-allowed"
					>
						{deleting ? 'Deleting...' : 'Delete'}
					</button>
				</div>
				<Button type="submit" disabled={loading || deleting}>
					{#if loading}
						Saving...
					{:else}
						Save Changes
					{/if}
				</Button>
			</div>
		</form>
	</div>
{/if}
