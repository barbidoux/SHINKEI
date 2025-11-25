/**
 * Types for AI-powered entity generation features
 */

// AI Provider constants and types
export const AI_PROVIDERS = ['openai', 'anthropic', 'ollama'] as const;
export type AIProvider = (typeof AI_PROVIDERS)[number];

// Provider-specific model suggestions
export const PROVIDER_MODELS: Record<AIProvider, string[]> = {
	openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
	anthropic: ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'],
	ollama: ['llama3.2', 'llama3.1', 'mistral', 'mixtral', 'codellama', 'phi3']
};

// Provider-specific temperature ranges
export const PROVIDER_TEMPERATURE_RANGES: Record<AIProvider, { min: number; max: number; default: number }> = {
	openai: { min: 0, max: 2, default: 0.7 },
	anthropic: { min: 0, max: 1, default: 0.7 },
	ollama: { min: 0, max: 2, default: 0.7 }
};

export interface EntitySuggestion {
    name: string;
    entity_type: 'character' | 'location';
    description?: string;
    confidence: number; // 0.0 to 1.0
    context_snippet?: string;
    metadata: Record<string, any>;
}

export interface EntitySuggestionsResponse {
    suggestions: EntitySuggestion[];
    total: number;
}

// Entity extraction

export interface ExtractEntitiesRequest {
    text: string;
    confidence_threshold?: number;
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
}

// Character generation

export interface GenerateCharacterRequest {
    story_id?: string;
    importance?: 'major' | 'minor' | 'background';
    role?: string;
    user_prompt?: string;
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
    temperature?: number;
}

// Location generation

export interface GenerateLocationRequest {
    parent_location_id?: string;
    location_type?: string;
    significance?: 'major' | 'minor' | 'background';
    user_prompt?: string;
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
    temperature?: number;
}

// Coherence validation

export interface ValidateEntityCoherenceRequest {
    entity_name: string;
    entity_type: 'character' | 'location';
    entity_description?: string;
    entity_metadata?: Record<string, any>;
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
}

export interface CoherenceValidationResponse {
    is_coherent: boolean;
    confidence_score: number;
    issues: string[];
    suggestions: string[];
    metadata: Record<string, any>;
}

// Description enhancement

export interface EnhanceEntityDescriptionRequest {
    entity_id: string;
    entity_type: 'character' | 'location';
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
    temperature?: number;
}

export interface EnhancedDescriptionResponse {
    original_description?: string;
    enhanced_description: string;
    entity_id: string;
    entity_type: string;
}

// ============================================================================
// Event Generation Types
// ============================================================================

export interface GenerateEventRequest {
    event_type?: string;
    time_range_min?: number;
    time_range_max?: number;
    location_id?: string;
    involving_character_ids?: string[];
    caused_by_event_ids?: string[];
    user_prompt?: string;
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
    temperature?: number;
}

export interface ExtractEventsFromBeatsRequest {
    beat_ids?: string[];
    confidence_threshold?: number;
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
}

export interface ValidateEventCoherenceRequest {
    event_summary: string;
    event_type: string;
    event_t: number;
    event_description?: string;
    location_id?: string;
    caused_by_event_ids?: string[];
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
}

export interface EventSuggestion {
    summary: string;
    event_type: string;
    description: string;
    t: number;
    label_time?: string;
    location_hint?: string;
    involved_characters: string[];
    caused_by_hints: string[];
    tags: string[];
    confidence: number;
    reasoning?: string;
}

export interface EventSuggestionsResponse {
    suggestions: EventSuggestion[];
    total: number;
}

export interface EventCoherenceValidationResponse {
    is_coherent: boolean;
    confidence_score: number;
    issues: string[];
    suggestions: string[];
    metadata: Record<string, any>;
}

// ============================================================================
// Story Template Generation Types
// ============================================================================

export interface GenerateStoryTemplateRequest {
    user_prompt?: string;
    preferred_mode?: 'autonomous' | 'collaborative' | 'manual';
    preferred_pov?: 'first' | 'third' | 'omniscient';
    target_length?: 'short' | 'medium' | 'long';
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
    temperature?: number;
}

export interface GeneratedTemplate {
    name: string;
    description: string;
    synopsis: string;
    theme: string;
    mode: string;
    pov_type: string;
    suggested_tags: string[];
    confidence: number;
    reasoning?: string;
}

export interface GenerateStoryOutlineRequest {
    story_id: string;
    num_acts?: number;
    beats_per_act?: number;
    include_world_events?: boolean;
    provider?: 'openai' | 'anthropic' | 'ollama';
    model?: string;
    temperature?: number;
}

export interface StoryOutlineAct {
    act_number: number;
    title: string;
    summary: string;
    beats: Record<string, any>[];
}

export interface StoryOutline {
    acts: StoryOutlineAct[];
    themes: string[];
    character_arcs: Record<string, any>[];
    estimated_beat_count: number;
    world_events_used: string[];
    metadata: Record<string, any>;
}

export interface SuggestTemplatesResponse {
    suggestions: string[];
    total: number;
}
