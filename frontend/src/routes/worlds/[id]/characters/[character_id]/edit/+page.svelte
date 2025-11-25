<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { addToast } from '$lib/stores/toast';
	import type { CharacterResponse, CharacterUpdate, EntityImportance } from '$lib/types/character';
	import { ENTITY_IMPORTANCE_OPTIONS, COMMON_CHARACTER_ROLES } from '$lib/types/character';
	import Button from '$lib/components/Button.svelte';
	import Breadcrumb from '$lib/components/Breadcrumb.svelte';
	import TagInput from '$lib/components/TagInput.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	const worldId = $page.params.id as string;
	const characterId = $page.params.character_id as string;

	let name = '';
	let description = '';
	let role = '';
	let importance: EntityImportance = 'background';
	let aliases: string[] = [];
	let loading = false;
	let loadingCharacter = true;
	let error = '';

	onMount(async () => {
		try {
			const character = await api.get<CharacterResponse>(
				`/worlds/${worldId}/characters/${characterId}`
			);
			name = character.name;
			description = character.description || '';
			role = character.role || '';
			importance = character.importance;
			aliases = character.aliases || [];
			loadingCharacter = false;
		} catch (e: any) {
			error = e.message || 'Failed to load character';
			loadingCharacter = false;
		}
	});

	async function handleSubmit() {
		if (!name.trim()) {
			error = 'Character name is required';
			return;
		}

		loading = true;
		error = '';

		try {
			const characterData: CharacterUpdate = {
				name: name.trim(),
				description: description.trim() || undefined,
				role: role.trim() || undefined,
				importance,
				aliases: aliases.length > 0 ? aliases : undefined
			};

			const response = await api.put<CharacterResponse>(
				`/worlds/${worldId}/characters/${characterId}`,
				characterData
			);

			addToast({
				type: 'success',
				message: `Character "${response.name}" updated successfully`
			});

			goto(`/worlds/${worldId}/characters/${characterId}`);
		} catch (e: any) {
			error = e.message || 'Failed to update character';
		} finally {
			loading = false;
		}
	}

	function handleCancel() {
		goto(`/worlds/${worldId}/characters/${characterId}`);
	}
</script>

<svelte:head>
	<title>Edit {name || 'Character'} - SHINKEI</title>
</svelte:head>

{#if loadingCharacter}
	<div class="flex items-center justify-center min-h-screen">
		<LoadingSpinner size="lg" text="Loading character..." />
	</div>
{:else if error && !name}
	<div class="flex items-center justify-center min-h-screen">
		<div class="text-center">
			<p class="text-red-500 dark:text-red-400 mb-4">{error}</p>
			<a
				href="/worlds/{worldId}/characters"
				class="text-indigo-600 dark:text-indigo-400 hover:text-indigo-500"
			>
				← Back to Characters
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
				{ label: 'Characters', href: `/worlds/${worldId}/characters` },
				{ label: name, href: `/worlds/${worldId}/characters/${characterId}` },
				{ label: 'Edit', href: `/worlds/${worldId}/characters/${characterId}/edit` }
			]}
		/>

		<!-- Header -->
		<div class="mb-8">
			<h1 class="text-3xl font-bold text-gray-900 dark:text-white">Edit Character</h1>
			<p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
				Update character information and metadata
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
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						The character's narrative role in the story
					</p>
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
					<p class="mt-1 text-xs text-gray-500 dark:text-gray-400">
						Detailed description of the character's traits, background, and appearance
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
