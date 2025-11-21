/**
 * Story-related TypeScript types matching backend schemas
 */

export type AuthoringMode = "autonomous" | "collaborative" | "manual";
export type POVType = "first" | "third" | "omniscient";
export type StoryStatus = "draft" | "in_progress" | "completed" | "archived";

export interface Story {
    id: string;
    world_id: string;
    title: string;
    synopsis?: string;
    theme?: string;
    status: StoryStatus;
    mode: AuthoringMode;
    pov_type: POVType;
    tags: string[];
    archived_at?: string;
    created_at: string;
    updated_at: string;
}

export interface StoryCreate {
    world_id: string;
    title: string;
    synopsis?: string;
    theme?: string;
    status?: StoryStatus;
    mode?: AuthoringMode;
    pov_type?: POVType;
    tags?: string[];
}

export interface StoryUpdate {
    title?: string;
    synopsis?: string;
    theme?: string;
    status?: StoryStatus;
    mode?: AuthoringMode;
    pov_type?: POVType;
    tags?: string[];
}

export interface StoryResponse extends Story {}

export interface StoryListResponse {
    stories: StoryResponse[];
    total: number;
    page: number;
    page_size: number;
}

export interface StoryStatistics {
    story_id: string;
    beat_count: number;
    word_count: number;
    character_count: number;
    ai_generated_count: number;
    user_generated_count: number;
    collaborative_count: number;
    latest_beat_date?: string;
    world_event_links: number;
    beat_type_distribution: Record<string, number>;
    estimated_reading_minutes: number;
}

export interface StoryTemplate {
    name: string;
    description: string;
    synopsis?: string;
    theme?: string;
    mode: AuthoringMode;
    pov_type: POVType;
    suggested_tags: string[];
}

// Helper labels for UI display
export const AUTHORING_MODE_LABELS: Record<AuthoringMode, string> = {
    autonomous: "Autonomous (AI generates everything)",
    collaborative: "Collaborative (AI + Human)",
    manual: "Manual (Human writes, AI assists)",
};

export const POV_TYPE_LABELS: Record<POVType, string> = {
    first: "First Person (I, we)",
    third: "Third Person (he, she, they)",
    omniscient: "Third Person Omniscient",
};

export const STORY_STATUS_LABELS: Record<StoryStatus, string> = {
    draft: "Draft",
    in_progress: "In Progress",
    completed: "Completed",
    archived: "Archived",
};
