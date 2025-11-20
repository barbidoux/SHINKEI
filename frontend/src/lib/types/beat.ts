/**
 * Story Beat-related TypeScript types matching backend schemas
 */

export type BeatType = "scene" | "log" | "memory" | "dialogue" | "description";
export type GeneratedBy = "ai" | "user" | "collaborative";

export interface StoryBeat {
    id: string;
    story_id: string;
    content: string;
    type: BeatType;
    order_index: number;
    summary?: string;
    local_time_label?: string;
    world_event_id?: string;
    generated_by: GeneratedBy;
    generation_reasoning?: string;
    created_at: string;
    updated_at: string;
}

export interface BeatCreate {
    story_id: string;
    content: string;
    type: BeatType;
    order_index: number;
    summary?: string;
    local_time_label?: string;
    world_event_id?: string;
    generated_by?: GeneratedBy;
}

export interface BeatUpdate {
    content?: string;
    type?: BeatType;
    order_index?: number;
    summary?: string;
    local_time_label?: string;
    world_event_id?: string;
    generation_reasoning?: string;
}

export interface BeatReasoningUpdate {
    generation_reasoning?: string;
}

export interface BeatResponse extends StoryBeat {}

export interface BeatListResponse {
    beats: BeatResponse[];
    total: number;
}

// Generation request/response types
export interface GenerateBeatRequest {
    provider?: string; // "openai" | "anthropic" | "ollama"
    model?: string;
    user_instructions?: string;
    target_event_id?: string;
    temperature?: number;
    max_tokens?: number;
    ollama_host?: string; // For custom Ollama server (Windows)
}

export interface SummarizeBeatRequest {
    provider?: string;
}

export interface SummarizeBeatResponse {
    beat_id: string;
    summary: string;
}

// Helper labels for UI display
export const BEAT_TYPE_LABELS: Record<BeatType, string> = {
    scene: "Scene",
    log: "Log Entry",
    memory: "Memory",
    dialogue: "Dialogue",
    description: "Description",
};

export const GENERATED_BY_LABELS: Record<GeneratedBy, string> = {
    ai: "AI Generated",
    user: "User Written",
    collaborative: "Collaborative",
};

// Beat Modification types
export interface BeatModificationRequest {
    modification_instructions: string;
    provider: "openai" | "anthropic" | "ollama";
    model?: string;
    ollama_host?: string;
    temperature?: number;
    max_tokens?: number;
    scope?: string[]; // ["content", "summary", "time_label", "world_event"]
}

export interface BeatModificationResponse {
    id: string;
    beat_id: string;

    // Original and modified versions
    original_content: string;
    modified_content: string;
    original_summary?: string;
    modified_summary?: string;
    original_time_label?: string;
    modified_time_label?: string;
    original_world_event_id?: string;
    modified_world_event_id?: string;

    // Metadata
    modification_instructions: string;
    reasoning?: string;
    unified_diff?: string;
    applied: boolean;
    created_at: string;
}

export interface BeatModificationApply {
    modification_id: string;
    apply_content?: boolean;
    apply_summary?: boolean;
    apply_time_label?: boolean;
    apply_world_event?: boolean;
}

export interface BeatModificationHistoryResponse {
    modifications: BeatModificationResponse[];
    total: number;
    beat_id: string;
}

// Beat Reordering
export interface BeatReorderRequest {
    beat_ids: string[];
}
