/**
 * Common API-related TypeScript types
 */

export interface PaginationParams {
    page?: number;
    page_size?: number;
    skip?: number;
    limit?: number;
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    page_size: number;
    pages: number;
}

export interface APIError {
    detail: string;
    status_code?: number;
    errors?: Record<string, string[]>;
}

export interface TokenResponse {
    access_token: string;
    token_type?: string;
    expires_in?: number;
}

export interface HealthCheckResponse {
    status: string;
    environment: string;
    version: string;
}

// LLM Provider types
export type LLMProvider = "openai" | "anthropic" | "ollama";

export interface LLMProviderConfig {
    provider: LLMProvider;
    model?: string;
    api_key?: string;
    base_url?: string; // For Ollama or custom endpoints
    temperature?: number;
    max_tokens?: number;
}

// Common response wrapper
export interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: APIError;
}
