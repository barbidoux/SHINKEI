<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Timeline } from 'vis-timeline/standalone';
	import type { TimelineOptions } from 'vis-timeline/types';
	import 'vis-timeline/styles/vis-timeline-graph2d.css';

	export let entityId: string;
	export let entityType: 'character' | 'location';
	export let entityName: string;
	export let apiUrl: string = '';
	export let height: string = '500px';

	interface EntityMention {
		story_beat_id: string;
		story_id: string;
		story_title: string;
		beat_order_index: number;
		mention_type: string;
		context_snippet?: string;
		created_at: string;
	}

	interface EntityTimelineResponse {
		entity_id: string;
		entity_type: string;
		entity_name: string;
		mentions: EntityMention[];
		total_mentions: number;
	}

	let container: HTMLElement;
	let timeline: Timeline | null = null;
	let loading = true;
	let error = '';
	let mentions: EntityMention[] = [];

	onMount(async () => {
		try {
			// Fetch timeline data
			const response = await fetch(
				`${apiUrl}/api/v1/entities/${entityType}/${entityId}/timeline`,
				{
					headers: {
						Authorization: `Bearer ${localStorage.getItem('auth_token')}`
					}
				}
			);

			if (!response.ok) {
				throw new Error('Failed to load entity timeline');
			}

			const data: EntityTimelineResponse = await response.json();
			mentions = data.mentions;

			if (mentions.length === 0) {
				error = `${entityName} has not appeared in any story beats yet.`;
				loading = false;
				return;
			}

			renderTimeline();
			loading = false;
		} catch (e: any) {
			error = e.message || 'Failed to load entity timeline';
			loading = false;
		}
	});

	function renderTimeline() {
		// Convert mentions to timeline items
		const items = mentions.map((mention, index) => {
			const content = mention.context_snippet
				? truncate(mention.context_snippet, 60)
				: `Beat ${mention.beat_order_index + 1}`;

			return {
				id: mention.story_beat_id,
				content: content,
				start: index, // Use sequential index as time
				title: `Story: ${mention.story_title}\nBeat ${mention.beat_order_index + 1}\nType: ${mention.mention_type}\n\n${mention.context_snippet || 'No context'}`,
				className: getMentionTypeClass(mention.mention_type),
				type: 'box',
				group: mention.story_id
			};
		});

		// Create groups for stories
		const uniqueStories = Array.from(
			new Map(mentions.map((m) => [m.story_id, m.story_title])).entries()
		);

		const groups = uniqueStories.map(([id, title]) => ({
			id,
			content: title,
			className: 'timeline-story-group'
		}));

		const options: TimelineOptions = {
			width: '100%',
			height: height,
			zoomable: true,
			moveable: true,
			zoomMin: 1000 * 60 * 60 * 24, // 1 day
			zoomMax: 1000 * 60 * 60 * 24 * 365 * 10, // 10 years
			orientation: { axis: 'top', item: 'top' },
			showCurrentTime: false,
			showMajorLabels: true,
			showMinorLabels: true,
			stack: true,
			verticalScroll: true,
			zoomKey: 'ctrlKey'
		};

		timeline = new Timeline(container, items, groups, options);

		// Handle click events - navigate to story beat
		timeline.on('select', (properties) => {
			if (properties.items.length > 0) {
				const selectedId = properties.items[0] as string;
				const selectedMention = mentions.find((m) => m.story_beat_id === selectedId);
				if (selectedMention) {
					// Navigate to story beat detail
					window.location.href = `/stories/${selectedMention.story_id}#beat-${selectedId}`;
				}
			}
		});
	}

	function getMentionTypeClass(type: string): string {
		const typeMap: Record<string, string> = {
			explicit: 'timeline-explicit',
			implicit: 'timeline-implicit',
			referenced: 'timeline-referenced'
		};
		return typeMap[type] || 'timeline-default';
	}

	function truncate(text: string, maxLength: number): string {
		if (text.length <= maxLength) return text;
		return text.substring(0, maxLength) + '...';
	}

	onDestroy(() => {
		if (timeline) {
			timeline.destroy();
		}
	});
</script>

<div class="entity-timeline-container">
	{#if loading}
		<div class="flex items-center justify-center h-96 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
			<div class="text-center">
				<svg
					class="animate-spin h-8 w-8 mx-auto mb-2 text-indigo-600 dark:text-indigo-400"
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
				<p class="text-gray-600 dark:text-gray-400">Loading timeline...</p>
			</div>
		</div>
	{:else if error}
		<div class="text-center py-12 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700">
			<svg
				xmlns="http://www.w3.org/2000/svg"
				class="h-12 w-12 mx-auto text-gray-400 mb-3"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<p class="text-sm text-gray-600 dark:text-gray-400">{error}</p>
		</div>
	{:else}
		<div class="timeline-header mb-4">
			<h3 class="text-lg font-semibold text-gray-900 dark:text-white">
				{entityName} Timeline
			</h3>
			<p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
				{mentions.length} appearance{mentions.length !== 1 ? 's' : ''} across {new Set(
					mentions.map((m) => m.story_id)
				).size} stor{new Set(mentions.map((m) => m.story_id)).size === 1 ? 'y' : 'ies'}
			</p>
			<p class="text-xs text-gray-400 dark:text-gray-500 mt-1">
				Scroll to pan • Ctrl + Scroll to zoom • Click boxes to view story beats
			</p>
		</div>

		<!-- Legend -->
		<div class="timeline-legend flex flex-wrap gap-3 mb-4 text-xs">
			<div class="flex items-center gap-1">
				<div class="w-3 h-3 rounded timeline-explicit"></div>
				<span class="text-gray-600 dark:text-gray-400">Explicit</span>
			</div>
			<div class="flex items-center gap-1">
				<div class="w-3 h-3 rounded timeline-implicit"></div>
				<span class="text-gray-600 dark:text-gray-400">Implicit</span>
			</div>
			<div class="flex items-center gap-1">
				<div class="w-3 h-3 rounded timeline-referenced"></div>
				<span class="text-gray-600 dark:text-gray-400">Referenced</span>
			</div>
		</div>

		<!-- Timeline Container -->
		<div
			bind:this={container}
			class="timeline-vis-container rounded-lg border border-gray-300 dark:border-gray-600 shadow-sm"
		></div>
	{/if}
</div>

<style>
	.entity-timeline-container {
		width: 100%;
	}

	.timeline-vis-container {
		background: white;
	}

	:global(.dark) .timeline-vis-container {
		background: #1f2937;
	}

	/* Mention type colors */
	:global(.timeline-explicit) {
		background-color: #10b981 !important; /* Green */
		border-color: #059669 !important;
		color: white !important;
	}

	:global(.timeline-implicit) {
		background-color: #f59e0b !important; /* Yellow */
		border-color: #d97706 !important;
		color: white !important;
	}

	:global(.timeline-referenced) {
		background-color: #6b7280 !important; /* Gray */
		border-color: #4b5563 !important;
		color: white !important;
	}

	:global(.timeline-default) {
		background-color: #6366f1 !important; /* Indigo */
		border-color: #4f46e5 !important;
		color: white !important;
	}

	/* Story group styling */
	:global(.timeline-story-group) {
		background-color: #f3f4f6 !important;
		border-color: #d1d5db !important;
		font-weight: 600 !important;
		color: #1f2937 !important;
	}

	:global(.dark .timeline-story-group) {
		background-color: #374151 !important;
		border-color: #4b5563 !important;
		color: #f9fafb !important;
	}

	/* Override vis-timeline default styles */
	:global(.vis-timeline) {
		border: none !important;
	}

	:global(.vis-item) {
		border-radius: 4px !important;
		font-size: 11px !important;
		font-weight: 500 !important;
	}

	:global(.vis-item.vis-selected) {
		border-color: #4f46e5 !important;
		box-shadow: 0 0 0 2px #818cf8 !important;
	}

	:global(.vis-labelset .vis-label) {
		border-right: 1px solid #e5e7eb !important;
	}

	:global(.dark .vis-labelset .vis-label) {
		border-right-color: #4b5563 !important;
		color: #f9fafb !important;
	}

	:global(.vis-time-axis .vis-text) {
		color: #6b7280 !important;
	}

	:global(.dark .vis-time-axis .vis-text) {
		color: #9ca3af !important;
	}

	:global(.vis-panel.vis-background) {
		background: white !important;
	}

	:global(.dark .vis-panel.vis-background) {
		background: #1f2937 !important;
	}

	:global(.vis-panel.vis-center) {
		background: white !important;
	}

	:global(.dark .vis-panel.vis-center) {
		background: #1f2937 !important;
	}
</style>
