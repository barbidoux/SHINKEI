<script lang="ts">
    import { onMount, onDestroy } from 'svelte';
    import { Timeline } from 'vis-timeline/standalone';
    import type { WorldEvent } from '$lib/types';
    import type { TimelineItem, TimelineOptions } from '$lib/types/timeline';
    import 'vis-timeline/styles/vis-timeline-graph2d.css';

    export let events: WorldEvent[] = [];
    export let onEventClick: ((event: WorldEvent) => void) | null = null;
    export let height: string = '400px';

    let container: HTMLElement;
    let timeline: Timeline | null = null;

    // Extended WorldEvent type that may include computed fields
    type WorldEventExtended = WorldEvent & { beat_count?: number };

    // Convert WorldEvents to Timeline items
    $: items = events.map((event): TimelineItem => {
        // beat_count is an optional computed field that may be present in extended responses
        const beatCount = (event as WorldEventExtended).beat_count;
        const beatCountLabel = beatCount ? ` (${beatCount} beats)` : '';
        return {
            id: event.id,
            content: `${event.label_time || `t=${event.t}`}: ${event.summary}${beatCountLabel}`,
            start: event.t,
            title: `${event.type} - ${event.location || 'Unknown location'}\n\nClick to view details`,
            className: getEventTypeClass(event.type),
            type: 'box'
        };
    });

    function getEventTypeClass(type: string): string {
        const typeMap: Record<string, string> = {
            political: 'timeline-political',
            environmental: 'timeline-environmental',
            technological: 'timeline-technological',
            social: 'timeline-social',
            military: 'timeline-military',
            economic: 'timeline-economic',
            cultural: 'timeline-cultural'
        };
        return typeMap[type] || 'timeline-default';
    }

    onMount(() => {
        const options: TimelineOptions = {
            width: '100%',
            height: height,
            zoomable: true,
            moveable: true,
            zoomMin: 100,
            zoomMax: 1000000000,
            orientation: 'top',
            showCurrentTime: false,
            showMajorLabels: true,
            showMinorLabels: true
        };

        // Cast to any to avoid type mismatch with vis-timeline's internal types
        timeline = new Timeline(container, items, options as any);

        // Handle click events
        timeline.on('select', (properties) => {
            if (properties.items.length > 0 && onEventClick) {
                const selectedId = properties.items[0];
                const selectedEvent = events.find(e => e.id === selectedId);
                if (selectedEvent) {
                    onEventClick(selectedEvent);
                }
            }
        });
    });

    onDestroy(() => {
        if (timeline) {
            timeline.destroy();
        }
    });

    // Update timeline when items change
    $: if (timeline && items) {
        timeline.setItems(items);
    }
</script>

<div class="world-timeline-container">
    <div class="timeline-header mb-4">
        <h3 class="text-lg font-semibold text-gray-900">World Event Timeline</h3>
        <p class="text-sm text-gray-500 mt-1">
            Scroll to pan • Scroll + Ctrl to zoom • Click events for details
        </p>
    </div>

    <!-- Legend -->
    <div class="timeline-legend flex flex-wrap gap-3 mb-4 text-xs">
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 rounded timeline-political"></div>
            <span>Political</span>
        </div>
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 rounded timeline-environmental"></div>
            <span>Environmental</span>
        </div>
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 rounded timeline-technological"></div>
            <span>Technological</span>
        </div>
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 rounded timeline-social"></div>
            <span>Social</span>
        </div>
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 rounded timeline-military"></div>
            <span>Military</span>
        </div>
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 rounded timeline-economic"></div>
            <span>Economic</span>
        </div>
        <div class="flex items-center gap-1">
            <div class="w-3 h-3 rounded timeline-cultural"></div>
            <span>Cultural</span>
        </div>
    </div>

    <!-- Timeline Container -->
    <div bind:this={container} class="timeline-vis-container rounded-lg border border-gray-300 shadow-sm"></div>

    {#if events.length === 0}
        <div class="text-center py-12 bg-gray-50 rounded-lg mt-4 border border-gray-200">
            <p class="text-sm text-gray-500">
                No events to display on timeline. Create world events to see them here.
            </p>
        </div>
    {/if}
</div>

<style>
    .world-timeline-container {
        width: 100%;
    }

    .timeline-vis-container {
        background: white;
    }

    /* Custom event type colors matching Shinkei theme */
    :global(.timeline-political) {
        background-color: #6366f1 !important; /* Indigo */
        border-color: #4f46e5 !important;
        color: white !important;
    }

    :global(.timeline-environmental) {
        background-color: #10b981 !important; /* Green */
        border-color: #059669 !important;
        color: white !important;
    }

    :global(.timeline-technological) {
        background-color: #8b5cf6 !important; /* Purple */
        border-color: #7c3aed !important;
        color: white !important;
    }

    :global(.timeline-social) {
        background-color: #ec4899 !important; /* Pink */
        border-color: #db2777 !important;
        color: white !important;
    }

    :global(.timeline-military) {
        background-color: #ef4444 !important; /* Red */
        border-color: #dc2626 !important;
        color: white !important;
    }

    :global(.timeline-economic) {
        background-color: #f59e0b !important; /* Amber */
        border-color: #d97706 !important;
        color: white !important;
    }

    :global(.timeline-cultural) {
        background-color: #06b6d4 !important; /* Cyan */
        border-color: #0891b2 !important;
        color: white !important;
    }

    :global(.timeline-default) {
        background-color: #6b7280 !important; /* Gray */
        border-color: #4b5563 !important;
        color: white !important;
    }

    /* Override vis-timeline default styles */
    :global(.vis-timeline) {
        border: none !important;
    }

    :global(.vis-item) {
        border-radius: 4px !important;
        font-size: 12px !important;
        font-weight: 500 !important;
    }

    :global(.vis-item.vis-selected) {
        box-shadow: 0 0 0 2px #6366f1 !important;
    }

    :global(.vis-time-axis .vis-text) {
        color: #374151 !important;
        font-size: 11px !important;
    }

    :global(.vis-time-axis .vis-grid.vis-major) {
        border-color: #e5e7eb !important;
    }

    :global(.vis-time-axis .vis-grid.vis-minor) {
        border-color: #f3f4f6 !important;
    }
</style>
