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
    target_length: Optional[int] = None
    pacing: Optional[str] = None  # "slow", "medium", "fast"
    tension_level: Optional[str] = None  # "low", "medium", "high"


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
