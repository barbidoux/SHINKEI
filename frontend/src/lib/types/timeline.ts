/**
 * Timeline visualization types for World Events
 */

export interface TimelineItem {
    id: string;
    content: string;
    start: Date | string | number;
    title?: string;
    className?: string;
    type?: 'box' | 'point' | 'range';
    group?: string;
}

export interface TimelineOptions {
    width?: string;
    height?: string;
    minHeight?: string;
    maxHeight?: string;
    zoomable?: boolean;
    moveable?: boolean;
    zoomMin?: number;
    zoomMax?: number;
    orientation?: 'top' | 'bottom' | 'both';
    showCurrentTime?: boolean;
    showMajorLabels?: boolean;
    showMinorLabels?: boolean;
    timeAxis?: {
        scale?: string;
        step?: number;
    };
}

export interface TimelineEventData {
    id: string;
    t: number;
    label_time?: string;
    summary: string;
    type: string;
    location?: string;
    beat_count?: number;
}
