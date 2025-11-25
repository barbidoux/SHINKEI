"""Service layer for AI-powered entity generation, extraction, and validation."""
from typing import Optional, List, Dict, Any
from shinkei.generation.base import (
    GenerationConfig,
    EntitySuggestion,
    EntityExtractionContext,
    CharacterGenerationContext,
    LocationGenerationContext,
    CoherenceValidationContext,
    CoherenceValidationResult
)
from shinkei.generation.factory import ModelFactory
from shinkei.generation.utils.json_truncation import (
    smart_truncate_json,
    smart_truncate_list,
    smart_truncate_metadata,
    truncate_text_for_extraction,
    MAX_TEXT_LENGTH
)
from shinkei.config import settings
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

# HIGH PRIORITY FIX 2.2: Provider-specific temperature ranges
PROVIDER_TEMPERATURE_RANGES = {
    "openai": {"min": 0.0, "max": 2.0, "default": 0.7},
    "anthropic": {"min": 0.0, "max": 1.0, "default": 0.7},
    "ollama": {"min": 0.0, "max": 2.0, "default": 0.7},
}


class EntityGenerationService:
    """Service for handling AI-powered entity operations."""

    def __init__(self, provider: Optional[str] = None, host: Optional[str] = None):
        """
        Initialize entity generation service.

        Args:
            provider: AI provider to use (default: from settings.default_llm_provider)
            host: Base URL for the provider (used for Ollama custom hosts)
        """
        self.default_provider = provider or settings.default_llm_provider
        self.host = host
        logger.info("entity_generation_service_initialized", provider=self.default_provider, host=host)

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
        HIGH PRIORITY FIX 2.2: Validate and clamp temperature to provider-specific range.

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

    def _deduplicate_suggestions(
        self,
        suggestions: List[EntitySuggestion]
    ) -> List[EntitySuggestion]:
        """
        HIGH PRIORITY FIX 2.3: Deduplicate entity suggestions by name, keeping highest confidence.

        Args:
            suggestions: List of entity suggestions

        Returns:
            Deduplicated list with highest confidence per entity
        """
        seen: Dict[tuple, EntitySuggestion] = {}

        for suggestion in suggestions:
            key = (suggestion.name.lower().strip(), suggestion.entity_type)
            if key not in seen or suggestion.confidence > seen[key].confidence:
                seen[key] = suggestion
                if key in seen and suggestion.confidence > seen[key].confidence:
                    logger.debug(
                        "duplicate_entity_replaced",
                        name=suggestion.name,
                        entity_type=suggestion.entity_type,
                        new_confidence=suggestion.confidence
                    )

        deduplicated = list(seen.values())
        if len(deduplicated) < len(suggestions):
            logger.info(
                "entities_deduplicated",
                original_count=len(suggestions),
                deduplicated_count=len(deduplicated)
            )

        return deduplicated

    async def extract_entities_from_text(
        self,
        text: str,
        world_data: Dict[str, Any],
        existing_characters: List[Dict[str, Any]],
        existing_locations: List[Dict[str, Any]],
        confidence_threshold: float = 0.7,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[EntitySuggestion]:
        """
        Extract entities (characters, locations) from narrative text.

        Args:
            text: Narrative text to analyze
            world_data: World context (name, tone, backdrop, laws)
            existing_characters: List of existing characters in the world
            existing_locations: List of existing locations in the world
            confidence_threshold: Minimum confidence to include (0.0 to 1.0)
            provider: AI provider to use (optional)
            model: Specific model to use (optional)

        Returns:
            List of EntitySuggestion objects
        """
        # HIGH PRIORITY FIX 2.5: Warn about extreme confidence thresholds
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

        # MEDIUM PRIORITY FIX 3.1: Truncate text to prevent token overflow
        processed_text = truncate_text_for_extraction(text, MAX_TEXT_LENGTH)

        logger.info(
            "extracting_entities",
            world_name=world_data.get("name"),
            text_length=len(processed_text),
            original_length=len(text),
            was_truncated=len(processed_text) < len(text),
            provider=provider or self.default_provider
        )

        # Build context
        context = EntityExtractionContext(
            text=processed_text,
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            existing_characters=existing_characters,
            existing_locations=existing_locations,
            confidence_threshold=confidence_threshold
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(temperature=0.3, model=model, provider=provider)

        # Extract entities
        try:
            suggestions = await model_instance.extract_entities(context, config)

            # HIGH PRIORITY FIX 2.3: Deduplicate suggestions
            suggestions = self._deduplicate_suggestions(suggestions)

            logger.info(
                "entities_extracted",
                world_name=world_data.get("name"),
                num_entities=len(suggestions)
            )
            return suggestions
        except Exception as e:
            logger.error("entity_extraction_failed", error=str(e))
            raise

    async def generate_character_suggestions(
        self,
        world_data: Dict[str, Any],
        existing_characters: List[Dict[str, Any]],
        story_data: Optional[Dict[str, Any]] = None,
        recent_beats: Optional[List[Dict[str, Any]]] = None,
        importance: Optional[str] = None,
        role: Optional[str] = None,
        user_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> List[EntitySuggestion]:
        """
        Generate character suggestions based on world and story context.

        Args:
            world_data: World context (name, tone, backdrop, laws)
            existing_characters: List of existing characters in the world
            story_data: Optional story context (title, synopsis)
            recent_beats: Optional list of recent beats for story context
            importance: Importance level hint (major, minor, background)
            role: Optional role hint (e.g., "antagonist", "mentor")
            user_prompt: User instructions for character generation
            provider: AI provider to use (optional)
            model: Specific model to use (optional)
            temperature: Generation temperature (optional)

        Returns:
            List of character suggestions (typically 1-3 options)
        """
        logger.info(
            "generating_characters",
            world_name=world_data.get("name"),
            importance=importance,
            role=role,
            provider=provider or self.default_provider
        )

        # Build context
        context = CharacterGenerationContext(
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            story_title=story_data.get("title") if story_data else None,
            story_synopsis=story_data.get("synopsis") if story_data else None,
            recent_beats=recent_beats or [],
            existing_characters=existing_characters,
            importance=importance,
            role=role,
            user_prompt=user_prompt
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(temperature=temperature or 0.8, model=model, provider=provider)

        # Generate characters
        try:
            suggestions = await model_instance.generate_character(context, config)

            # HIGH PRIORITY FIX 2.3: Deduplicate suggestions
            suggestions = self._deduplicate_suggestions(suggestions)

            logger.info(
                "characters_generated",
                world_name=world_data.get("name"),
                num_characters=len(suggestions)
            )
            return suggestions
        except Exception as e:
            logger.error("character_generation_failed", error=str(e))
            raise

    async def generate_location_suggestions(
        self,
        world_data: Dict[str, Any],
        existing_locations: List[Dict[str, Any]],
        parent_location_data: Optional[Dict[str, Any]] = None,
        location_type: Optional[str] = None,
        significance: Optional[str] = None,
        user_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> List[EntitySuggestion]:
        """
        Generate location suggestions based on world context.

        Args:
            world_data: World context (name, tone, backdrop, laws)
            existing_locations: List of existing locations in the world
            parent_location_data: Optional parent location for sub-locations
            location_type: Location type hint (e.g., "city", "forest", "building")
            significance: Significance level hint (major, minor, background)
            user_prompt: User instructions for location generation
            provider: AI provider to use (optional)
            model: Specific model to use (optional)
            temperature: Generation temperature (optional)

        Returns:
            List of location suggestions (typically 1-3 options)
        """
        logger.info(
            "generating_locations",
            world_name=world_data.get("name"),
            location_type=location_type,
            significance=significance,
            provider=provider or self.default_provider
        )

        # Build context
        context = LocationGenerationContext(
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            existing_locations=existing_locations,
            parent_location=parent_location_data,
            location_type=location_type,
            significance=significance,
            user_prompt=user_prompt
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(temperature=temperature or 0.8, model=model, provider=provider)

        # Generate locations
        try:
            suggestions = await model_instance.generate_location(context, config)

            # HIGH PRIORITY FIX 2.3: Deduplicate suggestions
            suggestions = self._deduplicate_suggestions(suggestions)

            logger.info(
                "locations_generated",
                world_name=world_data.get("name"),
                num_locations=len(suggestions)
            )
            return suggestions
        except Exception as e:
            logger.error("location_generation_failed", error=str(e))
            raise

    async def validate_entity_coherence(
        self,
        entity_name: str,
        entity_type: str,
        entity_description: Optional[str],
        entity_metadata: Dict[str, Any],
        world_data: Dict[str, Any],
        existing_characters: List[Dict[str, Any]],
        existing_locations: List[Dict[str, Any]],
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> CoherenceValidationResult:
        """
        Validate that an entity is coherent with world rules and existing entities.

        Args:
            entity_name: Name of entity to validate
            entity_type: Type of entity ("character" or "location")
            entity_description: Entity description
            entity_metadata: Entity metadata
            world_data: World context (name, tone, backdrop, laws)
            existing_characters: List of existing characters in the world
            existing_locations: List of existing locations in the world
            provider: AI provider to use (optional)
            model: Specific model to use (optional)

        Returns:
            CoherenceValidationResult with issues and suggestions
        """
        logger.info(
            "validating_entity_coherence",
            entity_name=entity_name,
            entity_type=entity_type,
            world_name=world_data.get("name"),
            provider=provider or self.default_provider
        )

        # Build context
        context = CoherenceValidationContext(
            entity_name=entity_name,
            entity_type=entity_type,
            entity_description=entity_description,
            entity_metadata=entity_metadata,
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            existing_characters=existing_characters,
            existing_locations=existing_locations
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(temperature=0.3, model=model, provider=provider)

        # Validate coherence
        try:
            result = await model_instance.validate_entity_coherence(context, config)
            logger.info(
                "entity_coherence_validated",
                entity_name=entity_name,
                is_coherent=result.is_coherent,
                confidence_score=result.confidence_score
            )
            return result
        except Exception as e:
            logger.error("coherence_validation_failed", error=str(e))
            raise

    async def enhance_entity_description(
        self,
        entity_name: str,
        entity_type: str,
        current_description: Optional[str],
        world_data: Dict[str, Any],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> str:
        """
        Enhance an entity's description using AI.

        Args:
            entity_name: Name of the entity
            entity_type: Type of entity ("character" or "location")
            current_description: Existing description (if any)
            world_data: World context (name, tone, backdrop, laws)
            provider: AI provider to use (optional)
            model: Specific model to use (optional)
            temperature: Generation temperature (optional)

        Returns:
            Enhanced description text
        """
        logger.info(
            "enhancing_entity_description",
            entity_name=entity_name,
            entity_type=entity_type,
            world_name=world_data.get("name"),
            provider=provider or self.default_provider
        )

        # Build world context dict
        world_context = {
            "world_name": world_data.get("name", "Unknown"),
            "world_tone": world_data.get("tone", ""),
            "world_backdrop": world_data.get("backdrop", ""),
            "world_laws": world_data.get("laws", {})
        }

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(temperature=temperature or 0.7, model=model, max_tokens=500, provider=provider)

        # Enhance description
        try:
            enhanced = await model_instance.enhance_entity_description(
                entity_name=entity_name,
                entity_type=entity_type,
                current_description=current_description,
                world_context=world_context,
                config=config
            )
            logger.info(
                "entity_description_enhanced",
                entity_name=entity_name,
                entity_type=entity_type,
                description_length=len(enhanced)
            )
            return enhanced
        except Exception as e:
            logger.error("description_enhancement_failed", error=str(e))
            raise
