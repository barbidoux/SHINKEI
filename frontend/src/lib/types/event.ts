/**
 * World Event-related TypeScript types matching backend schemas
 */

export type EventType = "major" | "minor" | "background" | "catalyst";

export interface WorldEvent {
    id: string;
    world_id: string;
    t: number; // Objective world time
    label_time?: string; // Human-readable timestamp (e.g., "2177-03-15", "The Fall")
    location?: string;
    type: EventType;
    summary: string;
    description?: string;
    metadata?: Record<string, any>;
    created_at: string;
    updated_at: string;
}

export interface WorldEventCreate {
    world_id: string;
    t: number;
    label_time?: string;
    location?: string;
    type: EventType;
    summary: string;
    description?: string;
    metadata?: Record<string, any>;
}

export interface WorldEventUpdate {
    t?: number;
    label_time?: string;
    location?: string;
    type?: EventType;
    summary?: string;
    description?: string;
    metadata?: Record<string, any>;
}

export interface WorldEventResponse extends WorldEvent {}

export interface WorldEventListResponse {
    events: WorldEventResponse[];
    total: number;
    page: number;
    page_size: number;
}

// Helper labels for UI display
export const EVENT_TYPE_LABELS: Record<EventType, string> = {
    major: "Major Event",
    minor: "Minor Event",
    background: "Background Event",
    catalyst: "Catalyst Event",
};

export const EVENT_TYPE_DESCRIPTIONS: Record<EventType, string> = {
    major: "Significant events that shape the world's history",
    minor: "Smaller events that add detail to the world",
    background: "Ongoing conditions or ambient events",
    catalyst: "Events that trigger story progression",
};
