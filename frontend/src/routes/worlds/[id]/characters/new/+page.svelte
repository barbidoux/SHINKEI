<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type { CharacterCreate, CharacterResponse, EntityImportance } from '$lib/types/character';
	import { ENTITY_IMPORTANCE_OPTIONS, COMMON_CHARACTER_ROLES } from '$lib/types/character';
	import Button from '$lib/components/Button.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import TagInput from '$lib/components/TagInput.svelte';

	const worldId = $page.params.id as string;

	let name = '';
	let description = '';
	let role = '';
	let importance: EntityImportance = 'background';
	let aliases: string[] = [];
	let loading = false;
	let error = '';

	async function handleSubmit() {
		if (!name.trim()) {
			error = 'Character name is required';
			return;
		}

		loading = true;
		error = '';

		try {
			const characterData: CharacterCreate = {
				name: name.trim(),
				description: description.trim() || undefined,
				role: role.trim() || undefined,
				importance,
				aliases: aliases.length > 0 ? aliases : undefined
			};

			const response = await api.post<CharacterResponse>(
				`/worlds/${worldId}/characters`,
				characterData
			);

			addToast({
				type: 'success',
				message: `Character "${response.name}" created successfully`
			});

			goto(`/worlds/${worldId}/characters/${response.id}`);
		} catch (e: any) {
			error = e.message || 'Failed to create character';
			console.error('Error creating character:', e);
		} finally {
			loading = false;
		}
	}

	function handleCancel() {
		goto(`/worlds/${worldId}/characters`);
	}
</script>

<svelte:head>
	<title>New Character - SHINKEI</title>
</svelte:head>

<div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
	<!-- Breadcrumb -->
	<Breadcrumb
		items={[
			{ label: 'Worlds', href: '/worlds' },
			{ label: 'World', href: `/worlds/${worldId}` },
			{ label: 'Characters', href: `/worlds/${worldId}/characters` },
			{ label: 'New', href: `/worlds/${worldId}/characters/new` }
		]}
	/>

	<!-- Header -->
	<div class="mb-8">
		<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Create New Character</h1>
		<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
			Add a new character to your world
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
					placeholder="e.g., Aragorn, Hermione Granger"
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				/>
			</div>

			<!-- Role -->
			<div>
				<label for="role" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Role
				</label>
				<input
					type="text"
					id="role"
					bind:value={role}
					list="common-roles"
					placeholder="e.g., Protagonist, Mentor, Antagonist"
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				/>
				<datalist id="common-roles">
					{#each COMMON_CHARACTER_ROLES as commonRole}
						<option value={commonRole} />
					{/each}
				</datalist>
			</div>

			<!-- Importance -->
			<div>
				<label
					for="importance"
					class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
				>
					Importance
				</label>
				<select
					id="importance"
					bind:value={importance}
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				>
					{#each ENTITY_IMPORTANCE_OPTIONS as option}
						<option value={option.value}>{option.label}</option>
					{/each}
				</select>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					Major characters are main protagonists/antagonists, minor are supporting roles, background
					are mentioned but not central
				</p>
			</div>

			<!-- Aliases -->
			<div>
				<label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
					Aliases
				</label>
				<TagInput
					bind:tags={aliases}
					placeholder="Add alternative names (press Enter or comma)"
					maxTags={10}
				/>
				<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					Alternative names or titles for this character
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
					placeholder="Describe the character's appearance, personality, background..."
					class="block w-full rounded-md border-gray-300 dark:border-gray-600 dark:bg-gray-700 dark:text-white shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
				/>
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
					Create Character
				{/if}
			</Button>
		</div>
	</form>
</div>
