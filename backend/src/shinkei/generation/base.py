"""Base classes for AI generation."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from dataclasses import dataclass, field


class GenerationRequest(BaseModel):
    """Standardized request for AI generation."""
    prompt: str
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationResponse(BaseModel):
    """Standardized response from AI generation."""
    content: str
    model_used: str
    usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: Optional[str] = None


# Narrative-specific models

@dataclass
class GenerationConfig:
    """Configuration for narrative generation."""
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2000
    top_p: float = 0.9
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    top_k: Optional[int] = None  # Top-k sampling (provider-dependent)
    stop_sequences: Optional[List[str]] = None


@dataclass
class GenerationContext:
    """Context for narrative generation from World/Story/Beat data."""
    # World context
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Story context
    story_title: str
    story_synopsis: str
    story_pov_type: str  # first/third/omniscient
    story_mode: str  # autonomous/collaborative/manual

    # Recent beats for continuity
    recent_beats: List[Dict[str, Any]] = field(default_factory=list)

    # Target event (if any)
    target_world_event: Optional[Dict[str, Any]] = None

    # User instructions (for collaborative mode)
    user_instructions: Optional[str] = None

    # Generation constraints
    target_length: Optional[int] = None  # Word count target
    target_length_preset: Optional[str] = None  # "short", "medium", "long"
    pacing: Optional[str] = None  # "slow", "medium", "fast"
    tension_level: Optional[str] = None  # "low", "medium", "high"
    dialogue_density: Optional[str] = None  # "minimal", "moderate", "heavy"
    description_richness: Optional[str] = None  # "sparse", "balanced", "detailed"


@dataclass
class GeneratedBeat:
    """Result of narrative beat generation."""
    text: str  # Generated narrative content
    summary: str  # Short summary for UI
    local_time_label: str  # In-world timestamp
    reasoning: Optional[str] = None  # AI reasoning/thoughts behind generation
    world_event_id: Optional[str] = None  # Link to WorldEvent
    beat_type: str = "scene"  # scene/summary/note
    metadata: Dict[str, Any] = field(default_factory=dict)  # Model info, tokens, etc.


@dataclass
class ModificationContext:
    """Context for modifying an existing beat."""
    # Original beat data (required)
    original_content: str
    modification_instructions: str

    # World context (for maintaining coherence)
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Story context
    story_title: str
    story_synopsis: str
    story_pov_type: str

    # Original beat data (optional)
    original_summary: Optional[str] = None
    original_time_label: Optional[str] = None
    original_world_event_id: Optional[str] = None

    # Fields to modify (default: all)
    scope: List[str] = field(default_factory=lambda: ["content", "summary", "time_label", "world_event"])


@dataclass
class ModifiedBeat:
    """Result of beat modification."""
    modified_content: str
    modified_summary: Optional[str] = None
    modified_time_label: Optional[str] = None
    modified_world_event_id: Optional[str] = None
    reasoning: Optional[str] = None  # AI reasoning for the changes
    metadata: Dict[str, Any] = field(default_factory=dict)  # Model info, tokens, etc.


# Entity generation models

@dataclass
class EntitySuggestion:
    """AI-suggested entity extracted or generated."""
    name: str
    entity_type: str  # "character" or "location"
    description: Optional[str] = None
    confidence: float = 1.0  # 0.0 to 1.0
    context_snippet: Optional[str] = None  # Where it was detected
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional fields (role, aliases, location_type, etc.)


@dataclass
class CharacterGenerationContext:
    """Context for AI character generation."""
    # World context
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Story context (optional)
    story_title: Optional[str] = None
    story_synopsis: Optional[str] = None
    recent_beats: List[Dict[str, Any]] = field(default_factory=list)

    # Existing characters (for avoiding duplicates)
    existing_characters: List[Dict[str, Any]] = field(default_factory=list)

    # Generation constraints
    importance: Optional[str] = None  # "major", "minor", "background"
    role: Optional[str] = None  # Optional role hint
    user_prompt: Optional[str] = None  # User instructions


@dataclass
class LocationGenerationContext:
    """Context for AI location generation."""
    # World context
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Existing locations (for hierarchy and avoiding duplicates)
    existing_locations: List[Dict[str, Any]] = field(default_factory=list)

    # Parent location (if generating sub-location)
    parent_location: Optional[Dict[str, Any]] = None

    # Generation constraints
    location_type: Optional[str] = None  # Type hint
    significance: Optional[str] = None  # "Major", "Minor", "Background"
    user_prompt: Optional[str] = None  # User instructions


@dataclass
class EntityExtractionContext:
    """Context for extracting entities from text."""
    # Text to analyze
    text: str

    # World context for coherence
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Existing entities to avoid duplicates
    existing_characters: List[Dict[str, Any]] = field(default_factory=list)
    existing_locations: List[Dict[str, Any]] = field(default_factory=list)

    # Configuration
    confidence_threshold: float = 0.7  # Minimum confidence to include


@dataclass
class CoherenceValidationContext:
    """Context for validating entity coherence."""
    # Entity to validate (required fields first)
    entity_name: str
    entity_type: str  # "character" or "location"

    # World context (required)
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Entity metadata (optional with defaults)
    entity_description: Optional[str] = None
    entity_metadata: Dict[str, Any] = field(default_factory=dict)

    # Existing entities (optional with defaults)
    existing_characters: List[Dict[str, Any]] = field(default_factory=list)
    existing_locations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class CoherenceValidationResult:
    """Result of entity coherence validation."""
    is_coherent: bool
    confidence_score: float  # 0.0 to 1.0
    issues: List[str] = field(default_factory=list)  # Specific coherence issues
    suggestions: List[str] = field(default_factory=list)  # How to fix issues
    metadata: Dict[str, Any] = field(default_factory=dict)


# World Event generation models

@dataclass
class EventGenerationContext:
    """Context for AI world event generation."""
    # World context (required)
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]
    chronology_mode: str  # "linear", "branching", etc.

    # Existing world data
    existing_events: List[Dict[str, Any]] = field(default_factory=list)
    existing_characters: List[Dict[str, Any]] = field(default_factory=list)
    existing_locations: List[Dict[str, Any]] = field(default_factory=list)

    # Generation constraints
    event_type: Optional[str] = None  # Type hint (battle, discovery, political, etc.)
    time_range_min: Optional[float] = None  # Minimum t value
    time_range_max: Optional[float] = None  # Maximum t value
    location_id: Optional[str] = None  # Force specific location
    involving_character_ids: List[str] = field(default_factory=list)  # Characters to involve
    caused_by_event_ids: List[str] = field(default_factory=list)  # Causal chain
    user_prompt: Optional[str] = None  # User instructions


@dataclass
class EventExtractionContext:
    """Context for extracting world events from story beats."""
    # Beats to analyze
    beats: List[Dict[str, Any]]  # List of beat text/summaries

    # World context for coherence
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Existing events (to avoid duplicates)
    existing_events: List[Dict[str, Any]] = field(default_factory=list)

    # Configuration
    confidence_threshold: float = 0.7  # Minimum confidence to include


@dataclass
class EventSuggestion:
    """AI-suggested world event."""
    # Core event data
    summary: str  # Brief event description
    event_type: str  # battle, discovery, political, natural, etc.
    description: str  # Detailed event description

    # Timeline positioning
    t: float  # World timeline position
    label_time: Optional[str] = None  # Human-readable time ("Year 42", "Dawn of Era 3")

    # Relationships
    location_hint: Optional[str] = None  # Suggested location name/ID
    involved_characters: List[str] = field(default_factory=list)  # Character names/IDs
    caused_by_hints: List[str] = field(default_factory=list)  # Parent event hints

    # Generation metadata
    tags: List[str] = field(default_factory=list)
    confidence: float = 1.0  # 0.0 to 1.0
    reasoning: Optional[str] = None  # AI explanation for the event


@dataclass
class EventCoherenceContext:
    """Context for validating event coherence."""
    # Event to validate (required fields first)
    event_summary: str
    event_type: str
    event_t: float
    event_description: str

    # World context (required)
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]
    chronology_mode: str

    # Event relationships (optional with defaults)
    event_location_id: Optional[str] = None
    event_caused_by_ids: List[str] = field(default_factory=list)

    # Existing data for validation (optional with defaults)
    existing_events: List[Dict[str, Any]] = field(default_factory=list)
    existing_characters: List[Dict[str, Any]] = field(default_factory=list)
    existing_locations: List[Dict[str, Any]] = field(default_factory=list)


# Story Template generation models

@dataclass
class TemplateGenerationContext:
    """Context for AI story template generation."""
    # World context (required)
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # User preferences
    user_prompt: Optional[str] = None  # e.g., "noir detective story"
    preferred_mode: Optional[str] = None  # autonomous/collaborative/manual
    preferred_pov: Optional[str] = None  # first/third/omniscient
    target_length: Optional[str] = None  # short/medium/long

    # Existing templates (to avoid duplicates)
    existing_templates: List[str] = field(default_factory=list)


@dataclass
class OutlineGenerationContext:
    """Context for generating story outlines."""
    # World context (required)
    world_name: str
    world_tone: str
    world_backdrop: str
    world_laws: Dict[str, Any]

    # Story context
    story_title: str
    story_synopsis: str
    story_theme: Optional[str] = None

    # Generation parameters
    num_acts: int = 3
    beats_per_act: int = 5
    include_world_events: bool = True

    # Available world data
    existing_events: List[Dict[str, Any]] = field(default_factory=list)
    existing_characters: List[Dict[str, Any]] = field(default_factory=list)
    existing_locations: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class GeneratedTemplate:
    """AI-generated story template."""
    name: str
    description: str
    synopsis: str
    theme: str
    mode: str  # autonomous/collaborative/manual
    pov_type: str  # first/third/omniscient
    suggested_tags: List[str] = field(default_factory=list)
    confidence: float = 1.0
    reasoning: Optional[str] = None


@dataclass
class StoryOutline:
    """AI-generated story outline."""
    acts: List[Dict[str, Any]]  # List of acts with beat summaries
    themes: List[str]  # Identified themes
    character_arcs: List[Dict[str, Any]]  # Character progression points
    estimated_beat_count: int
    world_events_used: List[str] = field(default_factory=list)  # Event IDs to incorporate
    metadata: Dict[str, Any] = field(default_factory=dict)


class NarrativeModel(ABC):
    """Abstract base class for narrative AI models."""

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate text based on the request.
        
        Args:
            request: GenerationRequest object
            
        Returns:
            GenerationResponse object
        """
        pass

    @abstractmethod
    async def stream(self, request: GenerationRequest) -> AsyncGenerator[str, None]:
        """
        Stream generated text.

        Args:
            request: GenerationRequest object

        Yields:
            Chunks of generated text
        """
        pass

    # Narrative-specific methods

    @abstractmethod
    async def generate_next_beat(
        self,
        context: GenerationContext,
        config: GenerationConfig
    ) -> GeneratedBeat:
        """
        Generate the next story beat based on narrative context.

        This is the core method for narrative generation, taking into account:
        - World rules, tone, and backdrop
        - Story synopsis, POV, and mode
        - Recent beats for continuity
        - Optional target WorldEvent to write toward
        - User instructions for collaborative mode

        Args:
            context: Full narrative context (World + Story + Beats)
            config: Generation parameters (temperature, tokens, etc.)

        Returns:
            GeneratedBeat with text, summary, time label, and metadata
        """
        pass

    @abstractmethod
    async def summarize(self, text: str) -> str:
        """
        Generate a concise summary of narrative text.

        Used to create beat summaries for UI display and context building.

        Args:
            text: Narrative text to summarize

        Returns:
            2-3 sentence summary
        """
        pass

    @abstractmethod
    async def modify_beat(
        self,
        context: "ModificationContext",
        config: GenerationConfig
    ) -> "ModifiedBeat":
        """
        Modify an existing story beat based on user instructions.

        Takes the original beat content and user modification instructions,
        then generates a modified version while maintaining narrative coherence.

        Args:
            context: Modification context with original beat and instructions
            config: Generation parameters (temperature, tokens, etc.)

        Returns:
            ModifiedBeat with modified content, summary, and reasoning
        """
        pass

    @abstractmethod
    async def generate_next_beat_stream(
        self,
        context: GenerationContext,
        config: GenerationConfig
    ) -> AsyncGenerator[str, None]:
        """
        Stream the next story beat content progressively.

        Similar to generate_next_beat but yields content tokens as they're generated,
        allowing for real-time display in the UI.

        Args:
            context: Full narrative context (World + Story + Beats)
            config: Generation parameters (temperature, tokens, etc.)

        Yields:
            Content chunks as they're generated
        """
        pass

    @abstractmethod
    async def generate_beat_metadata(
        self,
        content: str,
        context: GenerationContext
    ) -> GeneratedBeat:
        """
        Generate metadata (summary, time label, reasoning) for already-generated content.

        Used after streaming beat content to extract structured metadata.

        Args:
            content: The full beat content that was generated
            context: Narrative context for coherent metadata generation

        Returns:
            GeneratedBeat with empty text field but populated metadata fields
        """
        pass

    # Entity generation methods

    @abstractmethod
    async def extract_entities(
        self,
        context: EntityExtractionContext,
        config: GenerationConfig
    ) -> List[EntitySuggestion]:
        """
        Extract entities (characters, locations) from narrative text.

        Analyzes the provided text and identifies characters and locations mentioned,
        returning suggestions with confidence scores and context snippets.

        Args:
            context: Text to analyze plus world context for coherence
            config: Generation parameters

        Returns:
            List of EntitySuggestion objects with detected entities
        """
        pass

    @abstractmethod
    async def generate_character(
        self,
        context: CharacterGenerationContext,
        config: GenerationConfig
    ) -> List[EntitySuggestion]:
        """
        Generate character suggestions based on world and story context.

        Creates new character ideas that fit the world's tone, laws, and backdrop,
        optionally considering existing characters and story context.

        Args:
            context: World context, existing characters, and constraints
            config: Generation parameters

        Returns:
            List of character suggestions (typically 1-3 options)
        """
        pass

    @abstractmethod
    async def generate_location(
        self,
        context: LocationGenerationContext,
        config: GenerationConfig
    ) -> List[EntitySuggestion]:
        """
        Generate location suggestions based on world context.

        Creates new location ideas that fit the world's geography and lore,
        respecting hierarchical relationships with existing locations.

        Args:
            context: World context, existing locations, parent location
            config: Generation parameters

        Returns:
            List of location suggestions (typically 1-3 options)
        """
        pass

    @abstractmethod
    async def validate_entity_coherence(
        self,
        context: CoherenceValidationContext,
        config: GenerationConfig
    ) -> CoherenceValidationResult:
        """
        Validate that an entity is coherent with world rules and existing entities.

        Checks for:
        - Conflicts with world laws (physics, metaphysics, social rules)
        - Tone mismatches (e.g., comedic character in grimdark world)
        - Name conflicts with existing entities
        - Logical inconsistencies (e.g., location hierarchy violations)

        Args:
            context: Entity to validate plus world context
            config: Generation parameters

        Returns:
            CoherenceValidationResult with issues and suggestions
        """
        pass

    @abstractmethod
    async def enhance_entity_description(
        self,
        entity_name: str,
        entity_type: str,
        current_description: Optional[str],
        world_context: Dict[str, Any],
        config: GenerationConfig
    ) -> str:
        """
        Enhance an entity's description using AI.

        Takes an existing entity (with optional current description) and generates
        a richer, more detailed description that fits the world context.

        Args:
            entity_name: Name of the entity
            entity_type: "character" or "location"
            current_description: Existing description (if any)
            world_context: World name, tone, backdrop, laws
            config: Generation parameters

        Returns:
            Enhanced description text
        """
        pass

    # World Event generation methods

    @abstractmethod
    async def generate_world_event(
        self,
        context: "EventGenerationContext",
        config: GenerationConfig
    ) -> List["EventSuggestion"]:
        """
        Generate world event suggestions based on world context and constraints.

        Creates new world events that:
        - Respect world laws (physics, metaphysics, social rules)
        - Fit the world's tone and chronology mode
        - Connect to existing events via causal chains
        - Involve specified characters/locations when requested

        Args:
            context: World context, existing events, and generation constraints
            config: Generation parameters

        Returns:
            List of EventSuggestion objects (typically 1-3 options)
        """
        pass

    @abstractmethod
    async def extract_events_from_beats(
        self,
        context: "EventExtractionContext",
        config: GenerationConfig
    ) -> List["EventSuggestion"]:
        """
        Extract world-significant events from story beat text.

        Analyzes beats to identify events that should be recorded on the
        world timeline, distinguishing between:
        - Story-local events (not returned)
        - World-significant events (returned as suggestions)

        Args:
            context: Beats to analyze plus world context
            config: Generation parameters

        Returns:
            List of EventSuggestion objects representing world events
        """
        pass

    @abstractmethod
    async def validate_event_coherence(
        self,
        context: "EventCoherenceContext",
        config: GenerationConfig
    ) -> CoherenceValidationResult:
        """
        Validate that a world event is coherent with world rules and timeline.

        Checks for:
        - Conflicts with world laws (physics, metaphysics, social rules)
        - Timeline consistency (no paradoxes, proper causality)
        - Tone consistency with world's narrative style
        - Valid relationships to existing events, characters, locations

        Args:
            context: Event to validate plus world context
            config: Generation parameters

        Returns:
            CoherenceValidationResult with issues and suggestions
        """
        pass

    # Story Template generation methods

    @abstractmethod
    async def generate_story_template(
        self,
        context: "TemplateGenerationContext",
        config: GenerationConfig
    ) -> "GeneratedTemplate":
        """
        Generate a custom story template based on world and user preferences.

        Creates a story template that:
        - Fits the world's tone, laws, and backdrop
        - Matches user's preferred mode, POV, and length
        - Provides useful synopsis, theme, and tags

        Args:
            context: World context and user preferences
            config: Generation parameters

        Returns:
            GeneratedTemplate object
        """
        pass

    @abstractmethod
    async def generate_story_outline(
        self,
        context: "OutlineGenerationContext",
        config: GenerationConfig
    ) -> "StoryOutline":
        """
        Generate a story outline with act/beat structure.

        Creates a structured outline that:
        - Follows classic narrative structure (3-act, hero's journey, etc.)
        - Incorporates available world events where appropriate
        - Plans character arcs and development
        - Estimates total beat count

        Args:
            context: World and story context with generation parameters
            config: Generation parameters

        Returns:
            StoryOutline object with acts, themes, and character arcs
        """
        pass

    @abstractmethod
    async def suggest_templates_for_world(
        self,
        world_name: str,
        world_tone: str,
        world_backdrop: str,
        world_laws: Dict[str, Any],
        config: GenerationConfig
    ) -> List[str]:
        """
        Suggest appropriate story template types for a world.

        Analyzes the world's characteristics and suggests template types
        that would work well (e.g., "noir detective", "epic quest", "survival horror").

        Args:
            world_name: Name of the world
            world_tone: World's narrative tone
            world_backdrop: World setting description
            world_laws: World rules/laws
            config: Generation parameters

        Returns:
            List of template type suggestions (strings)
        """
        pass
