<script lang="ts">
	import type { CharacterResponse, CharacterWithMentionsResponse } from '$lib/types/character';
	import CharacterImportanceBadge from './CharacterImportanceBadge.svelte';

	export let character: CharacterResponse | CharacterWithMentionsResponse;
	export let worldId: string;

	function hasMentionCount(
		char: CharacterResponse | CharacterWithMentionsResponse
	): char is CharacterWithMentionsResponse {
		return 'mention_count' in char;
	}

	function truncate(text: string, maxLength: number): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}

	function stripHtml(html: string): string {
		const tmp = document.createElement('DIV');
		tmp.innerHTML = html;
		return tmp.textContent || tmp.innerText || '';
	}
</script>

<a
	href="/worlds/{worldId}/characters/{character.id}"
	class="block bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200 dark:border-gray-700 p-4"
>
	<div class="flex items-start justify-between mb-2">
		<h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate flex-1">
			{character.name}
		</h3>
		<CharacterImportanceBadge importance={character.importance} size="sm" />
	</div>

	{#if character.role}
		<p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
			{character.role}
		</p>
	{/if}

	{#if character.description}
		<p class="text-sm text-gray-500 dark:text-gray-400 line-clamp-2 mb-3">
			{truncate(stripHtml(character.description), 150)}
		</p>
	{/if}

	{#if character.aliases && character.aliases.length > 0}
		<div class="flex flex-wrap gap-1 mb-3">
			{#each character.aliases.slice(0, 3) as alias}
				<span
					class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200"
				>
					{alias}
				</span>
			{/each}
			{#if character.aliases.length > 3}
				<span class="text-xs text-gray-500 dark:text-gray-400 self-center">
					+{character.aliases.length - 3} more
				</span>
			{/if}
		</div>
	{/if}

	<div class="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
		<span>
			{#if hasMentionCount(character)}
				{character.mention_count} {character.mention_count === 1 ? 'mention' : 'mentions'}
			{/if}
		</span>
		<span>
			{new Date(character.created_at).toLocaleDateString()}
		</span>
	</div>
</a>
