"""Entity generation API endpoints for AI-powered entity operations."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from shinkei.auth.dependencies import get_current_user, get_db_session
from shinkei.models.user import User
from shinkei.config import settings
from shinkei.schemas.entity_generation import (
    ExtractEntitiesRequest,
    GenerateCharacterRequest,
    GenerateLocationRequest,
    ValidateEntityCoherenceRequest,
    EnhanceEntityDescriptionRequest,
    EntitySuggestionsResponse,
    EntitySuggestionResponse,
    CoherenceValidationResponse,
    EnhancedDescriptionResponse,
    # Event generation schemas
    GenerateEventRequest,
    ExtractEventsFromBeatsRequest,
    ValidateEventCoherenceRequest,
    EventSuggestionResponse,
    EventSuggestionsResponse,
    EventCoherenceValidationResponse,
    # Template generation schemas
    GenerateStoryTemplateRequest,
    GeneratedTemplateResponse,
    GenerateStoryOutlineRequest,
    StoryOutlineResponse,
    StoryOutlineActResponse,
    SuggestTemplatesRequest,
    SuggestTemplatesResponse
)
from shinkei.repositories.world import WorldRepository
from shinkei.repositories.story import StoryRepository
from shinkei.repositories.story_beat import StoryBeatRepository
from shinkei.repositories.character import CharacterRepository
from shinkei.repositories.location import LocationRepository
from shinkei.repositories.world_event import WorldEventRepository
from shinkei.generation.entity_generation_service import EntityGenerationService
from shinkei.generation.event_generation_service import EventGenerationService
from shinkei.generation.template_generation_service import TemplateGenerationService
from shinkei.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)


def _get_effective_provider(request_provider: Optional[str], user: User) -> str:
    """
    Get the effective provider based on request, user settings, and system default.

    Priority:
    1. Explicit request parameter (if provided)
    2. User settings llm_provider (if set)
    3. System default (settings.default_llm_provider)
    """
    if request_provider:
        return request_provider

    user_settings = user.settings or {}
    user_provider = user_settings.get("llm_provider") if isinstance(user_settings, dict) else None

    if user_provider:
        return user_provider

    return settings.default_llm_provider


def _get_effective_base_url(user: User) -> Optional[str]:
    """
    Get the effective base URL from user settings.

    Used primarily for Ollama to connect to custom hosts.
    """
    user_settings = user.settings or {}
    if isinstance(user_settings, dict):
        return user_settings.get("llm_base_url")
    return None


def _get_effective_model(request_model: Optional[str], user: User) -> Optional[str]:
    """
    Get the effective model based on request and user settings.

    Priority:
    1. Explicit request parameter (if provided)
    2. User settings llm_model (if set)
    3. None (let the provider use its default)
    """
    if request_model:
        return request_model

    user_settings = user.settings or {}
    if isinstance(user_settings, dict):
        return user_settings.get("llm_model")
    return None


def _build_world_data(world):
    """Build world data dict from world model."""
    return {
        "name": world.name,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws or {}
    }


def _build_story_data(story):
    """Build story data dict from story model."""
    return {
        "title": story.title,
        "synopsis": story.synopsis
    }


def _entity_suggestion_to_response(suggestion) -> EntitySuggestionResponse:
    """Convert EntitySuggestion to response schema."""
    return EntitySuggestionResponse(
        name=suggestion.name,
        entity_type=suggestion.entity_type,
        description=suggestion.description,
        confidence=suggestion.confidence,
        context_snippet=suggestion.context_snippet,
        metadata=suggestion.metadata
    )


@router.post(
    "/worlds/{world_id}/stories/{story_id}/beats/{beat_id}/extract-entities",
    response_model=EntitySuggestionsResponse,
    status_code=status.HTTP_200_OK
)
async def extract_entities_from_beat(
    world_id: str,
    story_id: str,
    beat_id: str,
    request: ExtractEntitiesRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Extract entities (characters, locations) from a story beat using AI.

    Analyzes the beat text and identifies mentioned characters and locations,
    returning suggestions with confidence scores.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Verify story ownership
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_world_and_id(world_id, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found in world {world_id}"
        )

    # Get beat
    beat_repo = StoryBeatRepository(session)
    beat = await beat_repo.get_by_story_and_id(story_id, beat_id)
    if not beat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Beat {beat_id} not found in story {story_id}"
        )

    # Get existing entities for the world
    char_repo = CharacterRepository(session)
    loc_repo = LocationRepository(session)

    characters, _ = await char_repo.list_by_world(world_id, skip=0, limit=100)
    locations, _ = await loc_repo.list_by_world(world_id, skip=0, limit=100)

    existing_characters = [
        {"name": c.name, "id": c.id, "role": c.role}
        for c in characters
    ]
    existing_locations = [
        {"name": l.name, "id": l.id, "location_type": l.location_type}
        for l in locations
    ]

    # Extract entities using service
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EntityGenerationService(provider=effective_provider, host=effective_base_url)
    world_data = _build_world_data(world)

    try:
        suggestions = await service.extract_entities_from_text(
            text=request.text,
            world_data=world_data,
            existing_characters=existing_characters,
            existing_locations=existing_locations,
            confidence_threshold=request.confidence_threshold,
            provider=effective_provider,
            model=effective_model
        )

        logger.info(
            "entities_extracted_from_beat",
            beat_id=beat_id,
            num_entities=len(suggestions),
            user_id=current_user.id
        )

        return EntitySuggestionsResponse(
            suggestions=[_entity_suggestion_to_response(s) for s in suggestions],
            total=len(suggestions)
        )

    except Exception as e:
        logger.error("entity_extraction_failed", error=str(e), beat_id=beat_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Entity extraction failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/characters/generate",
    response_model=EntitySuggestionsResponse,
    status_code=status.HTTP_200_OK
)
async def generate_character_suggestions(
    world_id: str,
    request: GenerateCharacterRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Generate character suggestions for a world using AI.

    Creates 3 character ideas that fit the world's tone, laws, and backdrop.
    Optionally uses story context for more relevant suggestions.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get existing characters
    char_repo = CharacterRepository(session)
    characters, _ = await char_repo.list_by_world(world_id, skip=0, limit=100)
    existing_characters = [
        {"name": c.name, "role": c.role, "importance": c.importance.value}
        for c in characters
    ]

    # Get story context if provided
    story_data = None
    recent_beats = []
    if request.story_id:
        story_repo = StoryRepository(session)
        story = await story_repo.get_by_world_and_id(world_id, request.story_id)
        if story:
            story_data = _build_story_data(story)

            # Get recent beats for context
            beat_repo = StoryBeatRepository(session)
            beats, _ = await beat_repo.list_by_story(request.story_id, skip=0, limit=5)
            recent_beats = [
                {"text": b.text, "summary": b.summary}
                for b in beats
            ]

    # Generate character suggestions
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EntityGenerationService(provider=effective_provider, host=effective_base_url)
    world_data = _build_world_data(world)

    try:
        suggestions = await service.generate_character_suggestions(
            world_data=world_data,
            existing_characters=existing_characters,
            story_data=story_data,
            recent_beats=recent_beats,
            importance=request.importance,
            role=request.role,
            user_prompt=request.user_prompt,
            provider=effective_provider,
            model=effective_model,
            temperature=request.temperature
        )

        logger.info(
            "characters_generated",
            world_id=world_id,
            num_characters=len(suggestions),
            user_id=current_user.id
        )

        return EntitySuggestionsResponse(
            suggestions=[_entity_suggestion_to_response(s) for s in suggestions],
            total=len(suggestions)
        )

    except Exception as e:
        logger.error("character_generation_failed", error=str(e), world_id=world_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Character generation failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/locations/generate",
    response_model=EntitySuggestionsResponse,
    status_code=status.HTTP_200_OK
)
async def generate_location_suggestions(
    world_id: str,
    request: GenerateLocationRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Generate location suggestions for a world using AI.

    Creates 3 location ideas that fit the world's geography and lore.
    Optionally creates sub-locations within a parent location.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get existing locations
    loc_repo = LocationRepository(session)
    locations, _ = await loc_repo.list_by_world(world_id, skip=0, limit=100)
    existing_locations = [
        {"name": l.name, "location_type": l.location_type, "significance": l.significance.value}
        for l in locations
    ]

    # Get parent location if provided
    parent_location_data = None
    if request.parent_location_id:
        parent = await loc_repo.get_by_world_and_id(world_id, request.parent_location_id)
        if parent:
            parent_location_data = {
                "name": parent.name,
                "description": parent.description,
                "location_type": parent.location_type
            }

    # Generate location suggestions
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EntityGenerationService(provider=effective_provider, host=effective_base_url)
    world_data = _build_world_data(world)

    try:
        suggestions = await service.generate_location_suggestions(
            world_data=world_data,
            existing_locations=existing_locations,
            parent_location_data=parent_location_data,
            location_type=request.location_type,
            significance=request.significance,
            user_prompt=request.user_prompt,
            provider=effective_provider,
            model=effective_model,
            temperature=request.temperature
        )

        logger.info(
            "locations_generated",
            world_id=world_id,
            num_locations=len(suggestions),
            user_id=current_user.id
        )

        return EntitySuggestionsResponse(
            suggestions=[_entity_suggestion_to_response(s) for s in suggestions],
            total=len(suggestions)
        )

    except Exception as e:
        logger.error("location_generation_failed", error=str(e), world_id=world_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Location generation failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/entities/validate-coherence",
    response_model=CoherenceValidationResponse,
    status_code=status.HTTP_200_OK
)
async def validate_entity_coherence(
    world_id: str,
    request: ValidateEntityCoherenceRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Validate that an entity is coherent with world rules using AI.

    Checks for:
    - World laws compliance (physics, metaphysics, technology level)
    - Tone consistency
    - Name conflicts with existing entities
    - Logical consistency (e.g., location hierarchy)
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get existing entities
    char_repo = CharacterRepository(session)
    loc_repo = LocationRepository(session)

    characters, _ = await char_repo.list_by_world(world_id, skip=0, limit=100)
    locations, _ = await loc_repo.list_by_world(world_id, skip=0, limit=100)

    existing_characters = [{"name": c.name} for c in characters]
    existing_locations = [{"name": l.name} for l in locations]

    # Validate coherence
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EntityGenerationService(provider=effective_provider, host=effective_base_url)
    world_data = _build_world_data(world)

    try:
        result = await service.validate_entity_coherence(
            entity_name=request.entity_name,
            entity_type=request.entity_type,
            entity_description=request.entity_description,
            entity_metadata=request.entity_metadata,
            world_data=world_data,
            existing_characters=existing_characters,
            existing_locations=existing_locations,
            provider=effective_provider,
            model=effective_model
        )

        logger.info(
            "entity_coherence_validated",
            world_id=world_id,
            entity_name=request.entity_name,
            is_coherent=result.is_coherent,
            user_id=current_user.id
        )

        return CoherenceValidationResponse(
            is_coherent=result.is_coherent,
            confidence_score=result.confidence_score,
            issues=result.issues,
            suggestions=result.suggestions,
            metadata=result.metadata
        )

    except Exception as e:
        logger.error("coherence_validation_failed", error=str(e), world_id=world_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Coherence validation failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/characters/{character_id}/enhance-description",
    response_model=EnhancedDescriptionResponse,
    status_code=status.HTTP_200_OK
)
async def enhance_character_description(
    world_id: str,
    character_id: str,
    request: EnhanceEntityDescriptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Enhance a character's description using AI.

    Takes the existing description and generates a richer, more detailed
    version that fits the world's tone and style.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get character
    char_repo = CharacterRepository(session)
    character = await char_repo.get_by_world_and_id(world_id, character_id)
    if not character:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Character {character_id} not found in world {world_id}"
        )

    # Enhance description
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EntityGenerationService(provider=effective_provider, host=effective_base_url)
    world_data = _build_world_data(world)

    try:
        enhanced = await service.enhance_entity_description(
            entity_name=character.name,
            entity_type="character",
            current_description=character.description,
            world_data=world_data,
            provider=effective_provider,
            model=effective_model,
            temperature=request.temperature
        )

        logger.info(
            "character_description_enhanced",
            character_id=character_id,
            world_id=world_id,
            user_id=current_user.id
        )

        return EnhancedDescriptionResponse(
            original_description=character.description,
            enhanced_description=enhanced,
            entity_id=character_id,
            entity_type="character"
        )

    except Exception as e:
        logger.error("description_enhancement_failed", error=str(e), character_id=character_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Description enhancement failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/locations/{location_id}/enhance-description",
    response_model=EnhancedDescriptionResponse,
    status_code=status.HTTP_200_OK
)
async def enhance_location_description(
    world_id: str,
    location_id: str,
    request: EnhanceEntityDescriptionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Enhance a location's description using AI.

    Takes the existing description and generates a richer, more atmospheric
    version that fits the world's tone and style.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get location
    loc_repo = LocationRepository(session)
    location = await loc_repo.get_by_world_and_id(world_id, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location {location_id} not found in world {world_id}"
        )

    # Enhance description
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EntityGenerationService(provider=effective_provider, host=effective_base_url)
    world_data = _build_world_data(world)

    try:
        enhanced = await service.enhance_entity_description(
            entity_name=location.name,
            entity_type="location",
            current_description=location.description,
            world_data=world_data,
            provider=effective_provider,
            model=effective_model,
            temperature=request.temperature
        )

        logger.info(
            "location_description_enhanced",
            location_id=location_id,
            world_id=world_id,
            user_id=current_user.id
        )

        return EnhancedDescriptionResponse(
            original_description=location.description,
            enhanced_description=enhanced,
            entity_id=location_id,
            entity_type="location"
        )

    except Exception as e:
        logger.error("description_enhancement_failed", error=str(e), location_id=location_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Description enhancement failed: {str(e)}"
        )


# ============================================================================
# World Event Generation Endpoints
# ============================================================================

def _event_suggestion_to_response(suggestion) -> EventSuggestionResponse:
    """Convert EventSuggestion dataclass to response schema."""
    return EventSuggestionResponse(
        summary=suggestion.summary,
        event_type=suggestion.event_type,
        description=suggestion.description,
        t=suggestion.t,
        label_time=suggestion.label_time,
        location_hint=suggestion.location_hint,
        involved_characters=suggestion.involved_characters,
        caused_by_hints=suggestion.caused_by_hints,
        tags=suggestion.tags,
        confidence=suggestion.confidence,
        reasoning=suggestion.reasoning
    )


@router.post(
    "/worlds/{world_id}/events/generate",
    response_model=EventSuggestionsResponse,
    status_code=status.HTTP_200_OK
)
async def generate_event_suggestions(
    world_id: str,
    request: GenerateEventRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Generate world event suggestions using AI.

    Creates 1-3 event ideas that fit the world's timeline, laws, and causality.
    Events can be constrained by time range, location, involved characters,
    and causal relationships to existing events.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get existing entities
    event_repo = WorldEventRepository(session)
    char_repo = CharacterRepository(session)
    loc_repo = LocationRepository(session)

    events, _ = await event_repo.list_by_world(world_id, skip=0, limit=100)
    characters, _ = await char_repo.list_by_world(world_id, skip=0, limit=100)
    locations, _ = await loc_repo.list_by_world(world_id, skip=0, limit=100)

    existing_events = [
        {
            "id": str(e.id),
            "summary": e.summary,
            "t": e.t,
            "event_type": e.type,
            "location_id": str(e.location_id) if e.location_id else None,
            "caused_by_ids": e.caused_by_ids or []
        }
        for e in events
    ]
    existing_characters = [
        {"id": str(c.id), "name": c.name, "importance": c.importance.value}
        for c in characters
    ]
    existing_locations = [
        {"id": str(l.id), "name": l.name, "location_type": l.location_type}
        for l in locations
    ]

    # Build world data
    world_data = {
        "name": world.name,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws or {},
        "chronology_mode": world.chronology_mode.value if world.chronology_mode else "linear"
    }

    # Generate event suggestions
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EventGenerationService(provider=effective_provider, host=effective_base_url)

    try:
        suggestions = await service.generate_event_suggestions(
            world_data=world_data,
            existing_events=existing_events,
            existing_characters=existing_characters,
            existing_locations=existing_locations,
            event_type=request.event_type,
            time_range_min=request.time_range_min,
            time_range_max=request.time_range_max,
            location_id=request.location_id,
            involving_character_ids=request.involving_character_ids,
            caused_by_event_ids=request.caused_by_event_ids,
            user_prompt=request.user_prompt,
            provider=effective_provider,
            model=effective_model,
            temperature=request.temperature
        )

        logger.info(
            "events_generated",
            world_id=world_id,
            num_events=len(suggestions),
            user_id=current_user.id
        )

        return EventSuggestionsResponse(
            suggestions=[_event_suggestion_to_response(s) for s in suggestions],
            total=len(suggestions)
        )

    except Exception as e:
        logger.error("event_generation_failed", error=str(e), world_id=world_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event generation failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/stories/{story_id}/extract-events",
    response_model=EventSuggestionsResponse,
    status_code=status.HTTP_200_OK
)
async def extract_events_from_story(
    world_id: str,
    story_id: str,
    request: ExtractEventsFromBeatsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Extract world-significant events from story beats using AI.

    Analyzes story beats to identify events that could be promoted to
    world events (events that affect the world beyond the story).
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Verify story exists in world
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_world_and_id(world_id, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found in world {world_id}"
        )

    # Get beats (either specific ones or all)
    beat_repo = StoryBeatRepository(session)
    if request.beat_ids:
        # Get specific beats
        beats = []
        for beat_id in request.beat_ids:
            beat = await beat_repo.get_by_story_and_id(story_id, beat_id)
            if beat:
                beats.append(beat)
    else:
        # Get all story beats
        beats, _ = await beat_repo.list_by_story(story_id, skip=0, limit=50)

    if not beats:
        return EventSuggestionsResponse(suggestions=[], total=0)

    # Get existing world events
    event_repo = WorldEventRepository(session)
    events, _ = await event_repo.list_by_world(world_id, skip=0, limit=100)

    beats_data = [
        {
            "id": str(b.id),
            "text": b.text,
            "summary": b.summary,
            "local_time_label": b.local_time_label,
            "seq_in_story": b.seq_in_story
        }
        for b in beats
    ]
    existing_events = [
        {
            "id": str(e.id),
            "summary": e.summary,
            "t": e.t,
            "event_type": e.type
        }
        for e in events
    ]

    # Build world data
    world_data = {
        "name": world.name,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws or {}
    }

    # Extract events
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EventGenerationService(provider=effective_provider, host=effective_base_url)

    try:
        suggestions = await service.extract_events_from_story_beats(
            beats=beats_data,
            world_data=world_data,
            existing_events=existing_events,
            confidence_threshold=request.confidence_threshold,
            provider=effective_provider,
            model=effective_model
        )

        logger.info(
            "events_extracted_from_story",
            world_id=world_id,
            story_id=story_id,
            num_beats_analyzed=len(beats),
            num_events_found=len(suggestions),
            user_id=current_user.id
        )

        return EventSuggestionsResponse(
            suggestions=[_event_suggestion_to_response(s) for s in suggestions],
            total=len(suggestions)
        )

    except Exception as e:
        logger.error("event_extraction_failed", error=str(e), story_id=story_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event extraction failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/events/validate-coherence",
    response_model=EventCoherenceValidationResponse,
    status_code=status.HTTP_200_OK
)
async def validate_event_coherence(
    world_id: str,
    request: ValidateEventCoherenceRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Validate that a world event is coherent with world rules using AI.

    Checks for:
    - World laws compliance (physics, metaphysics, technology level)
    - Timeline consistency (temporal order of causally linked events)
    - Causality chain validity (effects follow causes)
    - Tone consistency
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get existing entities for context
    event_repo = WorldEventRepository(session)
    char_repo = CharacterRepository(session)
    loc_repo = LocationRepository(session)

    events, _ = await event_repo.list_by_world(world_id, skip=0, limit=100)
    characters, _ = await char_repo.list_by_world(world_id, skip=0, limit=100)
    locations, _ = await loc_repo.list_by_world(world_id, skip=0, limit=100)

    existing_events = [
        {
            "id": str(e.id),
            "summary": e.summary,
            "t": e.t,
            "event_type": e.type,
            "caused_by_ids": e.caused_by_ids or []
        }
        for e in events
    ]
    existing_characters = [
        {"id": str(c.id), "name": c.name, "importance": c.importance.value}
        for c in characters
    ]
    existing_locations = [
        {"id": str(l.id), "name": l.name, "location_type": l.location_type}
        for l in locations
    ]

    # Build world data
    world_data = {
        "name": world.name,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws or {},
        "chronology_mode": world.chronology_mode.value if world.chronology_mode else "linear"
    }

    # Validate coherence
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = EventGenerationService(provider=effective_provider, host=effective_base_url)

    try:
        result = await service.validate_event_coherence(
            event_summary=request.event_summary,
            event_type=request.event_type,
            event_t=request.event_t,
            event_description=request.event_description or "",
            world_data=world_data,
            existing_events=existing_events,
            existing_characters=existing_characters,
            existing_locations=existing_locations,
            event_location_id=request.location_id,
            event_caused_by_ids=request.caused_by_event_ids,
            provider=effective_provider,
            model=effective_model
        )

        logger.info(
            "event_coherence_validated",
            world_id=world_id,
            event_summary=request.event_summary,
            is_coherent=result.is_coherent,
            user_id=current_user.id
        )

        return EventCoherenceValidationResponse(
            is_coherent=result.is_coherent,
            confidence_score=result.confidence_score,
            issues=result.issues,
            suggestions=result.suggestions,
            metadata=result.metadata
        )

    except Exception as e:
        logger.error("event_coherence_validation_failed", error=str(e), world_id=world_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Event coherence validation failed: {str(e)}"
        )


# ============================================================================
# Story Template Generation Endpoints
# ============================================================================

@router.post(
    "/worlds/{world_id}/templates/generate",
    response_model=GeneratedTemplateResponse,
    status_code=status.HTTP_200_OK
)
async def generate_story_template(
    world_id: str,
    request: GenerateStoryTemplateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Generate a custom story template using AI.

    Creates a story template that fits the world's tone, laws, and backdrop,
    based on user preferences for mode, POV, and story type.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Get existing templates (from story_templates module)
    from shinkei.generation.story_templates import TEMPLATES
    existing_templates = list(TEMPLATES.keys())

    # Build world data
    world_data = {
        "name": world.name,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws or {}
    }

    # Get effective provider, model, and base URL from request, user settings, or system default
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)

    # Generate template
    service = TemplateGenerationService(provider=effective_provider, host=effective_base_url)

    try:
        template = await service.generate_story_template(
            world_data=world_data,
            existing_templates=existing_templates,
            user_prompt=request.user_prompt,
            preferred_mode=request.preferred_mode,
            preferred_pov=request.preferred_pov,
            target_length=request.target_length,
            provider=effective_provider,
            model=effective_model,
            temperature=request.temperature
        )

        logger.info(
            "template_generated",
            world_id=world_id,
            template_name=template.name,
            user_id=current_user.id
        )

        return GeneratedTemplateResponse(
            name=template.name,
            description=template.description,
            synopsis=template.synopsis,
            theme=template.theme,
            mode=template.mode,
            pov_type=template.pov_type,
            suggested_tags=template.suggested_tags,
            confidence=template.confidence,
            reasoning=template.reasoning
        )

    except Exception as e:
        logger.error("template_generation_failed", error=str(e), world_id=world_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template generation failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/stories/{story_id}/outline/generate",
    response_model=StoryOutlineResponse,
    status_code=status.HTTP_200_OK
)
async def generate_story_outline(
    world_id: str,
    story_id: str,
    request: GenerateStoryOutlineRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Generate a story outline with act/beat structure using AI.

    Creates a structured outline that follows narrative patterns,
    incorporates available world events, and plans character arcs.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Verify story exists in world
    story_repo = StoryRepository(session)
    story = await story_repo.get_by_world_and_id(world_id, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Story {story_id} not found in world {world_id}"
        )

    # Get world events
    event_repo = WorldEventRepository(session)
    events, _ = await event_repo.list_by_world(world_id, skip=0, limit=50)
    world_events = [
        {
            "id": str(e.id),
            "summary": e.summary,
            "t": e.t,
            "event_type": e.type
        }
        for e in events
    ]

    # Get characters
    char_repo = CharacterRepository(session)
    characters, _ = await char_repo.list_by_world(world_id, skip=0, limit=50)
    existing_characters = [
        {"id": str(c.id), "name": c.name, "role": c.role, "importance": c.importance.value}
        for c in characters
    ]

    # Build data
    world_data = {
        "name": world.name,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws or {}
    }
    story_data = {
        "title": story.title,
        "synopsis": story.synopsis,
        "theme": story.theme
    }

    # Generate outline
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = TemplateGenerationService(provider=effective_provider, host=effective_base_url)

    try:
        outline = await service.generate_story_outline(
            story_data=story_data,
            world_data=world_data,
            world_events=world_events,
            existing_characters=existing_characters,
            num_acts=request.num_acts,
            beats_per_act=request.beats_per_act,
            include_world_events=request.include_world_events,
            provider=effective_provider,
            model=effective_model,
            temperature=request.temperature
        )

        logger.info(
            "outline_generated",
            world_id=world_id,
            story_id=story_id,
            num_acts=len(outline.acts),
            user_id=current_user.id
        )

        # Convert acts to response format
        acts_response = []
        for i, act in enumerate(outline.acts):
            acts_response.append(StoryOutlineActResponse(
                act_number=act.get("act_number", i + 1),
                title=act.get("title", f"Act {i + 1}"),
                summary=act.get("summary", ""),
                beats=act.get("beats", [])
            ))

        return StoryOutlineResponse(
            acts=acts_response,
            themes=outline.themes,
            character_arcs=outline.character_arcs,
            estimated_beat_count=outline.estimated_beat_count,
            world_events_used=outline.world_events_used,
            metadata=outline.metadata
        )

    except Exception as e:
        logger.error("outline_generation_failed", error=str(e), story_id=story_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Outline generation failed: {str(e)}"
        )


@router.post(
    "/worlds/{world_id}/templates/suggest",
    response_model=SuggestTemplatesResponse,
    status_code=status.HTTP_200_OK
)
async def suggest_templates_for_world(
    world_id: str,
    request: SuggestTemplatesRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
):
    """
    Get AI suggestions for story templates that fit a world.

    Returns a list of template/genre types (e.g., "detective noir", "epic quest")
    that would work well with the world's tone, laws, and backdrop.
    """
    # Verify world ownership
    world_repo = WorldRepository(session)
    world = await world_repo.get_by_user_and_id(current_user.id, world_id)
    if not world:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"World {world_id} not found or access denied"
        )

    # Build world data
    world_data = {
        "name": world.name,
        "tone": world.tone,
        "backdrop": world.backdrop,
        "laws": world.laws or {}
    }

    # Get suggestions
    effective_provider = _get_effective_provider(request.provider, current_user)
    effective_base_url = _get_effective_base_url(current_user)
    effective_model = _get_effective_model(request.model, current_user)
    service = TemplateGenerationService(provider=effective_provider, host=effective_base_url)

    try:
        suggestions = await service.suggest_templates_for_world(
            world_data=world_data,
            provider=effective_provider,
            model=effective_model
        )

        logger.info(
            "templates_suggested",
            world_id=world_id,
            num_suggestions=len(suggestions),
            user_id=current_user.id
        )

        return SuggestTemplatesResponse(
            suggestions=suggestions,
            total=len(suggestions)
        )

    except Exception as e:
        logger.error("template_suggestions_failed", error=str(e), world_id=world_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template suggestions failed: {str(e)}"
        )
