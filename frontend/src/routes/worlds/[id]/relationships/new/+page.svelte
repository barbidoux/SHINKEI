<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type {
		CharacterRelationshipCreate,
		CharacterRelationshipResponse,
		RelationshipStrength
	} from '$lib/types/relationship';
	import {
		RELATIONSHIP_STRENGTH_OPTIONS,
		COMMON_RELATIONSHIP_TYPES
	} from '$lib/types/relationship';
	import Button from '$lib/components/Button.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import EntityPicker from '$lib/components/EntityPicker.svelte';

	const worldId = $page.params.id as string;

	let characterAId = '';
	let characterBId = '';
	let relationshipType = '';
	let description = '';
	let strength: RelationshipStrength = 'moderate';
	let isMutual = true;
	let loading = false;
	let error = '';

	async function handleSubmit() {
		if (!characterAId) {
			error = 'Please select the first character';
			return;
		}
		if (!characterBId) {
			error = 'Please select the second character';
			return;
		}
		if (characterAId === characterBId) {
			error = 'Cannot create a relationship between the same character';
			return;
		}
		if (!relationshipType.trim()) {
			error = 'Relationship type is required';
			return;
		}

		loading = true;
		error = '';

		try {
			const relationshipData: CharacterRelationshipCreate = {
				character_a_id: characterAId,
				character_b_id: characterBId,
				relationship_type: relationshipType.trim(),
				description: description.trim() || undefined,
				strength,
				is_mutual: isMutual
			};

			const response = await api.post<CharacterRelationshipResponse>(
				`/worlds/${worldId}/character-relationships`,
				relationshipData
			);

			addToast({
				type: 'success',
				message: `Relationship created successfully`
			});

			goto(`/worlds/${worldId}/relationships`);
		} catch (e: any) {
			error = e.message || 'Failed to create relationship';
			console.error('Error creating relationship:', e);
		} finally {
			loading = false;
		}
	}

	function handleCancel() {
		goto(`/worlds/${worldId}/relationships`);
	}
</script>

<svelte:head>
	<title>New Relationship - SHINKEI</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Breadcrumb -->
	<Breadcrumb
		items={[
			{ label: 'Worlds', href: '/worlds' },
			{ label: 'World', href: `/worlds/${worldId}` },
			{ label: 'Relationships', href: `/worlds/${worldId}/relationships` },
			{ label: 'New', href: `/worlds/${worldId}/relationships/new` }
		]}
	/>

	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white">
			Create Character Relationship
		</h1>
		<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
			Define a connection between two characters
		</p>
	</div>

	<!-- Form -->
	<form on:submit|preventDefault={handleSubmit} class="space-y-6">
		<div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6 space-y-6">
			<!-- Character A -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					First Character <span class="text-red-500">*</span>
				</label>
				<EntityPicker
					{worldId}
					entityType="character"
					selectedEntityId={characterAId}
					onSelect={(id) => (characterAId = id)}
					placeholder="Select first character"
					excludeEntityId={characterBId}
				/>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					The character initiating or involved in this relationship
				</p>
			</div>

			<!-- Character B -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Second Character <span class="text-red-500">*</span>
				</label>
				<EntityPicker
					{worldId}
					entityType="character"
					selectedEntityId={characterBId}
					onSelect={(id) => (characterBId = id)}
					placeholder="Select second character"
					excludeEntityId={characterAId}
				/>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					The other character in this relationship
				</p>
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
					The nature of their connection (e.g., friendship, family, rivalry)
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
					Check if this relationship goes both ways (e.g., mutual friendship vs. one-sided
					admiration)
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
			<Button type="button" variant="secondary" on:click={handleCancel} disabled={loading}>
				Cancel
			</Button>
			<Button type="submit" disabled={loading}>
				{#if loading}
					Creating...
				{:else}
					Create Relationship
				{/if}
			</Button>
		</div>
	</form>
</div>
