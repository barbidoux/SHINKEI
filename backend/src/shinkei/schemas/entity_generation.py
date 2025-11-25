"""Entity generation Pydantic schemas for AI-powered entity operations."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from shinkei.security.validators import PlainText, SanitizedHTML


# Entity suggestion schemas (for extraction and generation results)

class EntitySuggestionResponse(BaseModel):
    """Schema for a single AI-generated or extracted entity suggestion."""
    name: str = Field(..., description="Entity name")
    entity_type: str = Field(..., pattern="^(character|location)$", description="Type of entity")
    description: Optional[str] = Field(None, description="Entity description")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    context_snippet: Optional[str] = Field(None, description="Text snippet where entity was detected")
    metadata: dict = Field(default_factory=dict, description="Additional metadata (role, aliases, location_type, etc.)")


class EntitySuggestionsResponse(BaseModel):
    """Schema for a list of entity suggestions."""
    suggestions: list[EntitySuggestionResponse]
    total: int


# Entity extraction schemas

class ExtractEntitiesRequest(BaseModel):
    """Schema for extracting entities from narrative text."""
    model_config = ConfigDict(extra='forbid')

    text: SanitizedHTML(50000) = Field(..., description="Narrative text to analyze")
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to include (0.0 to 1.0)"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use (defaults to configured default)"
    )
    model: Optional[str] = Field(None, description="Specific model to use (e.g., gpt-4o, claude-3-5-sonnet)")


# Character generation schemas

class GenerateCharacterRequest(BaseModel):
    """Schema for generating character suggestions."""
    model_config = ConfigDict(extra='forbid')

    story_id: Optional[str] = Field(None, description="Optional story ID for context")
    importance: Optional[str] = Field(
        None,
        pattern="^(major|minor|background)$",
        description="Importance level hint"
    )
    role: Optional[PlainText(200)] = Field(None, description="Optional role hint (e.g., 'antagonist', 'mentor')")
    user_prompt: Optional[SanitizedHTML(2000)] = Field(
        None,
        description="User instructions for character generation"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")


# Location generation schemas

class GenerateLocationRequest(BaseModel):
    """Schema for generating location suggestions."""
    model_config = ConfigDict(extra='forbid')

    parent_location_id: Optional[str] = Field(
        None,
        description="Optional parent location ID for generating sub-locations"
    )
    location_type: Optional[PlainText(100)] = Field(
        None,
        description="Location type hint (e.g., 'city', 'forest', 'building')"
    )
    significance: Optional[str] = Field(
        None,
        pattern="^(major|minor|background)$",
        description="Significance level hint"
    )
    user_prompt: Optional[SanitizedHTML(2000)] = Field(
        None,
        description="User instructions for location generation"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")


# Coherence validation schemas

class ValidateEntityCoherenceRequest(BaseModel):
    """Schema for validating entity coherence."""
    model_config = ConfigDict(extra='forbid')

    entity_name: PlainText(200) = Field(..., description="Name of entity to validate")
    entity_type: str = Field(..., pattern="^(character|location)$", description="Type of entity")
    entity_description: Optional[SanitizedHTML(10000)] = Field(None, description="Entity description")
    entity_metadata: dict = Field(default_factory=dict, description="Entity metadata")
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")


class CoherenceValidationResponse(BaseModel):
    """Schema for coherence validation result."""
    is_coherent: bool = Field(..., description="Whether entity is coherent with world")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in validation (0.0 to 1.0)")
    issues: list[str] = Field(default_factory=list, description="List of coherence issues found")
    suggestions: list[str] = Field(default_factory=list, description="Suggestions for fixing issues")
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (tone_match_score, lore_fit_score, etc.)"
    )


# Entity description enhancement schemas

class EnhanceEntityDescriptionRequest(BaseModel):
    """Schema for enhancing entity description."""
    model_config = ConfigDict(extra='forbid')

    entity_id: str = Field(..., description="ID of entity to enhance")
    entity_type: str = Field(..., pattern="^(character|location)$", description="Type of entity")
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")


class EnhancedDescriptionResponse(BaseModel):
    """Schema for enhanced description result."""
    original_description: Optional[str] = Field(None, description="Original description")
    enhanced_description: str = Field(..., description="AI-enhanced description")
    entity_id: str = Field(..., description="ID of entity that was enhanced")
    entity_type: str = Field(..., description="Type of entity")


# ============================================================================
# Event Generation Schemas
# ============================================================================

class GenerateEventRequest(BaseModel):
    """Schema for generating world event suggestions."""
    model_config = ConfigDict(extra='forbid')

    event_type: Optional[PlainText(100)] = Field(
        None,
        description="Event type hint (e.g., 'battle', 'discovery', 'political', 'natural', 'personal')"
    )
    time_range_min: Optional[float] = Field(
        None,
        description="Minimum t value for event placement on timeline"
    )
    time_range_max: Optional[float] = Field(
        None,
        description="Maximum t value for event placement on timeline"
    )
    location_id: Optional[str] = Field(
        None,
        description="Force event to occur at specific location ID"
    )
    involving_character_ids: list[str] = Field(
        default_factory=list,
        description="Character IDs that must be involved in the event"
    )
    caused_by_event_ids: list[str] = Field(
        default_factory=list,
        description="Event IDs that causally lead to this event"
    )
    user_prompt: Optional[SanitizedHTML(2000)] = Field(
        None,
        description="User instructions for event generation"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")


class ExtractEventsFromBeatsRequest(BaseModel):
    """Schema for extracting world events from story beats."""
    model_config = ConfigDict(extra='forbid')

    beat_ids: list[str] = Field(
        default_factory=list,
        description="Specific beat IDs to analyze (empty = all story beats)"
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to include (0.0 to 1.0)"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")


class ValidateEventCoherenceRequest(BaseModel):
    """Schema for validating world event coherence."""
    model_config = ConfigDict(extra='forbid')

    event_summary: PlainText(500) = Field(..., description="Brief event description")
    event_type: PlainText(100) = Field(..., description="Event type (battle, discovery, political, etc.)")
    event_t: float = Field(..., description="Timeline position")
    event_description: Optional[SanitizedHTML(10000)] = Field(None, description="Detailed event description")
    location_id: Optional[str] = Field(None, description="Location ID where event occurs")
    caused_by_event_ids: list[str] = Field(
        default_factory=list,
        description="Event IDs that causally lead to this event"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")


class EventSuggestionResponse(BaseModel):
    """Schema for a single AI-generated world event suggestion."""
    summary: str = Field(..., description="Brief event description")
    event_type: str = Field(..., description="Event type (battle, discovery, political, etc.)")
    description: str = Field(..., description="Detailed event description")
    t: float = Field(..., description="Suggested timeline position")
    label_time: Optional[str] = Field(None, description="Human-readable time label")
    location_hint: Optional[str] = Field(None, description="Suggested location name")
    involved_characters: list[str] = Field(default_factory=list, description="Suggested involved characters")
    caused_by_hints: list[str] = Field(default_factory=list, description="Causal event hints")
    tags: list[str] = Field(default_factory=list, description="Suggested tags")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)")
    reasoning: Optional[str] = Field(None, description="AI reasoning for this suggestion")


class EventSuggestionsResponse(BaseModel):
    """Schema for a list of event suggestions."""
    suggestions: list[EventSuggestionResponse]
    total: int


class EventCoherenceValidationResponse(BaseModel):
    """Schema for event coherence validation result."""
    is_coherent: bool = Field(..., description="Whether event is coherent with world")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in validation (0.0 to 1.0)")
    issues: list[str] = Field(default_factory=list, description="List of coherence issues found")
    suggestions: list[str] = Field(default_factory=list, description="Suggestions for fixing issues")
    metadata: dict = Field(
        default_factory=dict,
        description="Additional metadata (laws_check, timeline_check, causality_check, etc.)"
    )


# ============================================================================
# Story Template Generation Schemas
# ============================================================================

class GenerateStoryTemplateRequest(BaseModel):
    """Schema for generating AI story templates."""
    model_config = ConfigDict(extra='forbid')

    user_prompt: Optional[SanitizedHTML(2000)] = Field(
        None,
        description="User description of desired story type (e.g., 'noir detective story')"
    )
    preferred_mode: Optional[str] = Field(
        None,
        pattern="^(autonomous|collaborative|manual)$",
        description="Preferred authoring mode"
    )
    preferred_pov: Optional[str] = Field(
        None,
        pattern="^(first|third|omniscient)$",
        description="Preferred point of view"
    )
    target_length: Optional[str] = Field(
        None,
        pattern="^(short|medium|long)$",
        description="Target story length"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")


class GeneratedTemplateResponse(BaseModel):
    """Schema for AI-generated story template."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    synopsis: str = Field(..., description="Suggested story synopsis")
    theme: str = Field(..., description="Suggested theme")
    mode: str = Field(..., description="Suggested authoring mode")
    pov_type: str = Field(..., description="Suggested point of view")
    suggested_tags: list[str] = Field(default_factory=list, description="Suggested story tags")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence score")
    reasoning: Optional[str] = Field(None, description="AI reasoning for this template")


class GenerateStoryOutlineRequest(BaseModel):
    """Schema for generating story outlines."""
    model_config = ConfigDict(extra='forbid')

    story_id: str = Field(..., description="Story ID to generate outline for")
    num_acts: int = Field(default=3, ge=1, le=7, description="Number of acts (1-7)")
    beats_per_act: int = Field(default=5, ge=1, le=15, description="Beats per act (1-15)")
    include_world_events: bool = Field(
        default=True,
        description="Whether to incorporate existing world events"
    )
    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0, description="Generation temperature")


class StoryOutlineActResponse(BaseModel):
    """Schema for a single act in story outline."""
    act_number: int = Field(..., description="Act number (1-based)")
    title: str = Field(..., description="Act title")
    summary: str = Field(..., description="Act summary")
    beats: list[dict] = Field(default_factory=list, description="Beat summaries for this act")


class StoryOutlineResponse(BaseModel):
    """Schema for AI-generated story outline."""
    acts: list[StoryOutlineActResponse] = Field(..., description="List of acts")
    themes: list[str] = Field(default_factory=list, description="Identified themes")
    character_arcs: list[dict] = Field(default_factory=list, description="Character progression points")
    estimated_beat_count: int = Field(..., description="Estimated total beat count")
    world_events_used: list[str] = Field(default_factory=list, description="World event IDs incorporated")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SuggestTemplatesRequest(BaseModel):
    """Schema for getting AI template suggestions for a world."""
    model_config = ConfigDict(extra='forbid')

    provider: Optional[str] = Field(
        None,
        pattern="^(openai|anthropic|ollama)$",
        description="AI provider to use"
    )
    model: Optional[str] = Field(None, description="Specific model to use")


class SuggestTemplatesResponse(BaseModel):
    """Schema for template suggestions response."""
    suggestions: list[str] = Field(..., description="List of suggested template/genre types")
    total: int = Field(..., description="Number of suggestions")
