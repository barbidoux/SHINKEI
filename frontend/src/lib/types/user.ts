/**
 * User-related TypeScript types matching backend schemas
 */

export interface UserSettings {
    language: string;
    default_model: string;
    ui_theme: "light" | "dark" | "system";
    llm_provider: "openai" | "anthropic" | "ollama";
    llm_model: string;
    llm_base_url?: string;
}

export interface User {
    id: string;
    email: string;
    name: string;
    settings: UserSettings;
    created_at: string;
    updated_at: string;
}

export interface UserCreate {
    email: string;
    name: string;
    id?: string; // Optional, provided by Supabase Auth
    settings?: UserSettings;
}

export interface UserUpdate {
    name?: string;
    settings?: Partial<UserSettings>;
}

export interface UserResponse extends User {}

export interface UserListResponse {
    users: UserResponse[];
    total: number;
    page: number;
    page_size: number;
}
