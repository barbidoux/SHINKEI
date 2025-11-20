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
}

export interface StoryUpdate {
    title?: string;
    synopsis?: string;
    theme?: string;
    status?: StoryStatus;
    mode?: AuthoringMode;
    pov_type?: POVType;
}

export interface StoryResponse extends Story {}

export interface StoryListResponse {
    stories: StoryResponse[];
    total: number;
    page: number;
    page_size: number;
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
