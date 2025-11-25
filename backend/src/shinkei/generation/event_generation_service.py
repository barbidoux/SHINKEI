"""Service layer for AI-powered world event generation, extraction, and validation."""
from typing import Optional, List, Dict, Any
from shinkei.generation.base import (
    GenerationConfig,
    EventSuggestion,
    EventGenerationContext,
    EventExtractionContext,
    EventCoherenceContext,
    CoherenceValidationResult
)
from shinkei.generation.factory import ModelFactory
from shinkei.generation.utils.json_truncation import (
    smart_truncate_json,
    smart_truncate_list
)
from shinkei.config import settings
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

# Provider-specific temperature ranges (same as entity service)
PROVIDER_TEMPERATURE_RANGES = {
    "openai": {"min": 0.0, "max": 2.0, "default": 0.7},
    "anthropic": {"min": 0.0, "max": 1.0, "default": 0.7},
    "ollama": {"min": 0.0, "max": 2.0, "default": 0.7},
}


class EventGenerationService:
    """Service for handling AI-powered world event operations."""

    def __init__(self, provider: Optional[str] = None, host: Optional[str] = None):
        """
        Initialize event generation service.

        Args:
            provider: AI provider to use (default: from settings.default_llm_provider)
            host: Base URL for the provider (used for Ollama custom hosts)
        """
        self.default_provider = provider or settings.default_llm_provider
        self.host = host
        logger.info("event_generation_service_initialized", provider=self.default_provider, host=host)

    def _get_model(self, provider: Optional[str] = None, model_name: Optional[str] = None):
        """
        Get model instance for the specified provider.

        Args:
            provider: Provider name (openai, anthropic, ollama) or None for default
            model_name: Specific model to use

        Returns:
            NarrativeModel instance
        """
        provider = provider or self.default_provider
        return ModelFactory.create(provider, model_name=model_name, host=self.host)

    def _validate_temperature(
        self,
        temperature: Optional[float],
        provider: Optional[str] = None
    ) -> float:
        """
        Validate and clamp temperature to provider-specific range.

        Args:
            temperature: Requested temperature
            provider: Provider name

        Returns:
            Valid temperature for the provider
        """
        provider = provider or self.default_provider
        ranges = PROVIDER_TEMPERATURE_RANGES.get(provider, {"min": 0.0, "max": 2.0, "default": 0.7})

        if temperature is None:
            return ranges["default"]

        # Clamp to valid range
        if temperature < ranges["min"]:
            logger.warning(
                "temperature_clamped_to_min",
                requested=temperature,
                provider=provider,
                min_value=ranges["min"]
            )
            return ranges["min"]

        if temperature > ranges["max"]:
            logger.warning(
                "temperature_clamped_to_max",
                requested=temperature,
                provider=provider,
                max_value=ranges["max"]
            )
            return ranges["max"]

        return temperature

    def _build_config(
        self,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        provider: Optional[str] = None
    ) -> GenerationConfig:
        """
        Build generation config with defaults and validation.

        Args:
            temperature: Generation temperature (default: 0.7)
            model: Model name override
            max_tokens: Max tokens (default: 2000)
            provider: Provider for temperature validation

        Returns:
            GenerationConfig object
        """
        validated_temp = self._validate_temperature(temperature, provider)
        return GenerationConfig(
            model=model,
            temperature=validated_temp,
            max_tokens=max_tokens or 2000
        )

    def _deduplicate_event_suggestions(
        self,
        suggestions: List[EventSuggestion]
    ) -> List[EventSuggestion]:
        """
        Deduplicate event suggestions by summary, keeping highest confidence.

        Args:
            suggestions: List of event suggestions

        Returns:
            Deduplicated list with highest confidence per event
        """
        seen: Dict[str, EventSuggestion] = {}

        for suggestion in suggestions:
            # Use normalized summary as key
            key = suggestion.summary.lower().strip()
            if key not in seen or suggestion.confidence > seen[key].confidence:
                seen[key] = suggestion
                if key in seen and suggestion.confidence > seen[key].confidence:
                    logger.debug(
                        "duplicate_event_replaced",
                        summary=suggestion.summary,
                        new_confidence=suggestion.confidence
                    )

        deduplicated = list(seen.values())
        if len(deduplicated) < len(suggestions):
            logger.info(
                "events_deduplicated",
                original_count=len(suggestions),
                deduplicated_count=len(deduplicated)
            )

        return deduplicated

    async def generate_event_suggestions(
        self,
        world_data: Dict[str, Any],
        existing_events: List[Dict[str, Any]],
        existing_characters: List[Dict[str, Any]],
        existing_locations: List[Dict[str, Any]],
        event_type: Optional[str] = None,
        time_range_min: Optional[float] = None,
        time_range_max: Optional[float] = None,
        location_id: Optional[str] = None,
        involving_character_ids: Optional[List[str]] = None,
        caused_by_event_ids: Optional[List[str]] = None,
        user_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> List[EventSuggestion]:
        """
        Generate world event suggestions based on world context and constraints.

        Args:
            world_data: World context (name, tone, backdrop, laws, chronology_mode)
            existing_events: List of existing world events
            existing_characters: List of existing characters
            existing_locations: List of existing locations
            event_type: Optional event type hint (battle, discovery, political, etc.)
            time_range_min: Minimum t value for event placement
            time_range_max: Maximum t value for event placement
            location_id: Force event to occur at specific location
            involving_character_ids: Characters that must be involved
            caused_by_event_ids: Events that must cause this one (causality chain)
            user_prompt: User instructions for event generation
            provider: AI provider to use (optional)
            model: Specific model to use (optional)
            temperature: Generation temperature (optional)

        Returns:
            List of EventSuggestion objects (typically 1-3 options)
        """
        logger.info(
            "generating_world_events",
            world_name=world_data.get("name"),
            event_type=event_type,
            time_range=(time_range_min, time_range_max),
            provider=provider or self.default_provider
        )

        # Truncate large data to prevent token overflow
        truncated_events = smart_truncate_list(
            existing_events, max_items=20,
            key_fields=["id", "summary", "t", "event_type"]
        )
        truncated_characters = smart_truncate_list(
            existing_characters, max_items=30,
            key_fields=["id", "name", "importance"]
        )
        truncated_locations = smart_truncate_list(
            existing_locations, max_items=30,
            key_fields=["id", "name", "location_type"]
        )

        # Build context
        context = EventGenerationContext(
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            chronology_mode=world_data.get("chronology_mode", "linear"),
            existing_events=truncated_events,
            existing_characters=truncated_characters,
            existing_locations=truncated_locations,
            event_type=event_type,
            time_range_min=time_range_min,
            time_range_max=time_range_max,
            location_id=location_id,
            involving_character_ids=involving_character_ids or [],
            caused_by_event_ids=caused_by_event_ids or [],
            user_prompt=user_prompt
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(
            temperature=temperature or 0.7,  # Balanced for creativity + coherence
            model=model,
            max_tokens=3000,  # Events need more tokens for rich descriptions
            provider=provider
        )

        # Generate events
        try:
            suggestions = await model_instance.generate_world_event(context, config)

            # Deduplicate suggestions
            suggestions = self._deduplicate_event_suggestions(suggestions)

            logger.info(
                "world_events_generated",
                world_name=world_data.get("name"),
                num_events=len(suggestions)
            )
            return suggestions
        except Exception as e:
            logger.error("world_event_generation_failed", error=str(e))
            raise

    async def extract_events_from_story_beats(
        self,
        beats: List[Dict[str, Any]],
        world_data: Dict[str, Any],
        existing_events: List[Dict[str, Any]],
        confidence_threshold: float = 0.7,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[EventSuggestion]:
        """
        Extract world-significant events from story beat text.

        Args:
            beats: List of story beats to analyze
            world_data: World context (name, tone, backdrop, laws)
            existing_events: List of existing world events (to avoid duplicates)
            confidence_threshold: Minimum confidence to include (0.0 to 1.0)
            provider: AI provider to use (optional)
            model: Specific model to use (optional)

        Returns:
            List of EventSuggestion objects representing world events
        """
        # Validate inputs
        if not beats:
            logger.warning("extract_events_called_with_empty_beats")
            return []

        # Warn about extreme confidence thresholds
        if confidence_threshold >= 0.95:
            logger.warning(
                "high_confidence_threshold_may_filter_all",
                threshold=confidence_threshold,
                recommendation="Consider using 0.6-0.8 for best results"
            )
        elif confidence_threshold < 0.3:
            logger.warning(
                "low_confidence_threshold_may_include_noise",
                threshold=confidence_threshold,
                recommendation="Consider using 0.6-0.8 for best results"
            )

        logger.info(
            "extracting_events_from_beats",
            world_name=world_data.get("name"),
            num_beats=len(beats),
            provider=provider or self.default_provider
        )

        # Truncate beats to prevent token overflow
        truncated_beats = smart_truncate_list(
            beats, max_items=10,
            key_fields=["id", "text", "summary", "local_time_label"]
        )
        truncated_events = smart_truncate_list(
            existing_events, max_items=20,
            key_fields=["id", "summary", "t", "event_type"]
        )

        # Build context
        context = EventExtractionContext(
            beats=truncated_beats,
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            existing_events=truncated_events,
            confidence_threshold=confidence_threshold
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(
            temperature=0.3,  # Lower for more deterministic extraction
            model=model,
            max_tokens=3000,
            provider=provider
        )

        # Extract events
        try:
            suggestions = await model_instance.extract_events_from_beats(context, config)

            # Deduplicate suggestions
            suggestions = self._deduplicate_event_suggestions(suggestions)

            logger.info(
                "events_extracted_from_beats",
                world_name=world_data.get("name"),
                num_beats_analyzed=len(beats),
                num_events_found=len(suggestions)
            )
            return suggestions
        except Exception as e:
            logger.error("event_extraction_failed", error=str(e))
            raise

    async def validate_event_coherence(
        self,
        event_summary: str,
        event_type: str,
        event_t: float,
        event_description: str,
        world_data: Dict[str, Any],
        existing_events: List[Dict[str, Any]],
        existing_characters: List[Dict[str, Any]],
        existing_locations: List[Dict[str, Any]],
        event_location_id: Optional[str] = None,
        event_caused_by_ids: Optional[List[str]] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> CoherenceValidationResult:
        """
        Validate that a world event is coherent with world rules and timeline.

        Args:
            event_summary: Brief event description
            event_type: Event type (battle, discovery, political, etc.)
            event_t: Timeline position
            event_description: Detailed event description
            world_data: World context (name, tone, backdrop, laws, chronology_mode)
            existing_events: List of existing world events
            existing_characters: List of existing characters
            existing_locations: List of existing locations
            event_location_id: Location where event occurs (optional)
            event_caused_by_ids: Events that cause this one (optional)
            provider: AI provider to use (optional)
            model: Specific model to use (optional)

        Returns:
            CoherenceValidationResult with issues and suggestions
        """
        logger.info(
            "validating_event_coherence",
            event_summary=event_summary,
            event_type=event_type,
            event_t=event_t,
            world_name=world_data.get("name"),
            provider=provider or self.default_provider
        )

        # Truncate data to prevent token overflow
        truncated_events = smart_truncate_list(
            existing_events, max_items=30,
            key_fields=["id", "summary", "t", "event_type", "caused_by_ids"]
        )
        truncated_characters = smart_truncate_list(
            existing_characters, max_items=20,
            key_fields=["id", "name", "importance"]
        )
        truncated_locations = smart_truncate_list(
            existing_locations, max_items=20,
            key_fields=["id", "name", "location_type"]
        )

        # Build context
        context = EventCoherenceContext(
            event_summary=event_summary,
            event_type=event_type,
            event_t=event_t,
            event_description=event_description,
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            chronology_mode=world_data.get("chronology_mode", "linear"),
            event_location_id=event_location_id,
            event_caused_by_ids=event_caused_by_ids or [],
            existing_events=truncated_events,
            existing_characters=truncated_characters,
            existing_locations=truncated_locations
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(
            temperature=0.3,  # Lower for more deterministic validation
            model=model,
            max_tokens=2000,
            provider=provider
        )

        # Validate coherence
        try:
            result = await model_instance.validate_event_coherence(context, config)
            logger.info(
                "event_coherence_validated",
                event_summary=event_summary,
                is_coherent=result.is_coherent,
                confidence_score=result.confidence_score,
                num_issues=len(result.issues)
            )
            return result
        except Exception as e:
            logger.error("event_coherence_validation_failed", error=str(e))
            raise
