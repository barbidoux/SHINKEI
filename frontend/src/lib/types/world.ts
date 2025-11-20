/**
 * World-related TypeScript types matching backend schemas
 */

export type ChronologyMode = "linear" | "fragmented" | "timeless";

export interface WorldLaws {
    physics?: string;
    metaphysics?: string;
    social?: string;
    forbidden?: string;
}

export interface World {
    id: string;
    user_id: string;
    name: string;
    description?: string;
    tone?: string;
    backdrop?: string;
    laws: WorldLaws;
    chronology_mode: ChronologyMode;
    created_at: string;
    updated_at: string;
}

export interface WorldCreate {
    name: string;
    description?: string;
    tone?: string;
    backdrop?: string;
    laws?: WorldLaws;
    chronology_mode?: ChronologyMode;
}

export interface WorldUpdate {
    name?: string;
    description?: string;
    tone?: string;
    backdrop?: string;
    laws?: WorldLaws;
    chronology_mode?: ChronologyMode;
}

export interface WorldResponse extends World {}

export interface WorldListResponse {
    worlds: WorldResponse[];
    total: number;
    page: number;
    page_size: number;
}
