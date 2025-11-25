/**
 * API methods for AI-powered entity generation
 */
import { api } from '$lib/api';
import type {
    ExtractEntitiesRequest,
    GenerateCharacterRequest,
    GenerateLocationRequest,
    ValidateEntityCoherenceRequest,
    EnhanceEntityDescriptionRequest,
    EntitySuggestionsResponse,
    CoherenceValidationResponse,
    EnhancedDescriptionResponse
} from '$lib/types/entity-generation';

/**
 * Extract entities (characters, locations) from a story beat using AI
 */
export async function extractEntitiesFromBeat(
    worldId: string,
    storyId: string,
    beatId: string,
    request: ExtractEntitiesRequest
): Promise<EntitySuggestionsResponse> {
    return api.post<EntitySuggestionsResponse>(
        `/worlds/${worldId}/stories/${storyId}/beats/${beatId}/extract-entities`,
        request
    );
}

/**
 * Generate character suggestions for a world using AI
 */
export async function generateCharacterSuggestions(
    worldId: string,
    request: GenerateCharacterRequest
): Promise<EntitySuggestionsResponse> {
    return api.post<EntitySuggestionsResponse>(
        `/worlds/${worldId}/characters/generate`,
        request
    );
}

/**
 * Generate location suggestions for a world using AI
 */
export async function generateLocationSuggestions(
    worldId: string,
    request: GenerateLocationRequest
): Promise<EntitySuggestionsResponse> {
    return api.post<EntitySuggestionsResponse>(
        `/worlds/${worldId}/locations/generate`,
        request
    );
}

/**
 * Validate that an entity is coherent with world rules using AI
 */
export async function validateEntityCoherence(
    worldId: string,
    request: ValidateEntityCoherenceRequest
): Promise<CoherenceValidationResponse> {
    return api.post<CoherenceValidationResponse>(
        `/worlds/${worldId}/entities/validate-coherence`,
        request
    );
}

/**
 * Enhance a character's description using AI
 */
export async function enhanceCharacterDescription(
    worldId: string,
    characterId: string,
    request: EnhanceEntityDescriptionRequest
): Promise<EnhancedDescriptionResponse> {
    return api.post<EnhancedDescriptionResponse>(
        `/worlds/${worldId}/characters/${characterId}/enhance-description`,
        request
    );
}

/**
 * Enhance a location's description using AI
 */
export async function enhanceLocationDescription(
    worldId: string,
    locationId: string,
    request: EnhanceEntityDescriptionRequest
): Promise<EnhancedDescriptionResponse> {
    return api.post<EnhancedDescriptionResponse>(
        `/worlds/${worldId}/locations/${locationId}/enhance-description`,
        request
    );
}
