<script lang="ts">
    import { api } from '$lib/api';
    import type { ChatContext } from '$lib/types';

    export let context: ChatContext;

    // Names loaded from API
    let worldName = '';
    let storyTitle = '';
    let beatLabel = '';
    let characterName = '';
    let locationName = '';

    // Loading states
    let loadingWorld = false;
    let loadingStory = false;
    let loadingBeat = false;
    let loadingCharacter = false;
    let loadingLocation = false;

    // Load world name
    async function loadWorldName(id: string) {
        loadingWorld = true;
        try {
            const world = await api.get<{ name: string }>(`/worlds/${id}`);
            worldName = world.name;
        } catch {
            worldName = 'Unknown World';
        } finally {
            loadingWorld = false;
        }
    }

    // Load story title
    async function loadStoryTitle(id: string) {
        loadingStory = true;
        try {
            const story = await api.get<{ title: string }>(`/stories/${id}`);
            storyTitle = story.title;
        } catch {
            storyTitle = 'Unknown Story';
        } finally {
            loadingStory = false;
        }
    }

    // Load beat label
    async function loadBeatLabel(storyId: string, beatId: string) {
        loadingBeat = true;
        try {
            const beat = await api.get<{ order_index: number; summary?: string }>(`/stories/${storyId}/beats/${beatId}`);
            beatLabel = beat.summary ? `Beat ${beat.order_index}: ${beat.summary.slice(0, 20)}...` : `Beat ${beat.order_index}`;
        } catch {
            beatLabel = 'Unknown Beat';
        } finally {
            loadingBeat = false;
        }
    }

    // Load character name
    async function loadCharacterName(worldId: string, characterId: string) {
        loadingCharacter = true;
        try {
            const character = await api.get<{ name: string }>(`/worlds/${worldId}/characters/${characterId}`);
            characterName = character.name;
        } catch {
            characterName = 'Unknown Character';
        } finally {
            loadingCharacter = false;
        }
    }

    // Load location name
    async function loadLocationName(worldId: string, locationId: string) {
        loadingLocation = true;
        try {
            const location = await api.get<{ name: string }>(`/worlds/${worldId}/locations/${locationId}`);
            locationName = location.name;
        } catch {
            locationName = 'Unknown Location';
        } finally {
            loadingLocation = false;
        }
    }

    // Reactive loading based on context changes
    $: if (context.worldId) {
        loadWorldName(context.worldId);
    } else {
        worldName = '';
    }

    $: if (context.storyId) {
        loadStoryTitle(context.storyId);
    } else {
        storyTitle = '';
    }

    $: if (context.storyId && context.beatId) {
        loadBeatLabel(context.storyId, context.beatId);
    } else {
        beatLabel = '';
    }

    $: if (context.worldId && context.characterId) {
        loadCharacterName(context.worldId, context.characterId);
    } else {
        characterName = '';
    }

    $: if (context.worldId && context.locationId) {
        loadLocationName(context.worldId, context.locationId);
    } else {
        locationName = '';
    }

    $: hasContext = worldName || storyTitle || beatLabel || characterName || locationName;
</script>

<div class="flex flex-wrap gap-1.5 px-3 py-2 bg-gray-50 dark:bg-gray-900/50 text-xs border-b border-gray-200 dark:border-gray-700">
    {#if loadingWorld}
        <span class="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse">Loading...</span>
    {:else if worldName}
        <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-indigo-100 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 rounded">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {worldName}
        </span>
    {/if}

    {#if loadingStory}
        <span class="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse">Loading...</span>
    {:else if storyTitle}
        <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300 rounded">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            {storyTitle}
        </span>
    {/if}

    {#if loadingBeat}
        <span class="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse">Loading...</span>
    {:else if beatLabel}
        <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300 rounded">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {beatLabel}
        </span>
    {/if}

    {#if loadingCharacter}
        <span class="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse">Loading...</span>
    {:else if characterName}
        <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-300 rounded">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            {characterName}
        </span>
    {/if}

    {#if loadingLocation}
        <span class="px-2 py-0.5 bg-gray-200 dark:bg-gray-700 rounded animate-pulse">Loading...</span>
    {:else if locationName}
        <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-cyan-100 dark:bg-cyan-900/40 text-cyan-700 dark:text-cyan-300 rounded">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {locationName}
        </span>
    {/if}

    {#if !hasContext && !loadingWorld}
        <span class="text-gray-500 dark:text-gray-400 italic">
            Navigate to a world to enable context-aware assistance
        </span>
    {/if}
</div>
