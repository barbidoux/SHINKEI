"""Service layer for AI-powered story template generation."""
from typing import Optional, List, Dict, Any
from shinkei.generation.base import (
    GenerationConfig,
    GeneratedTemplate,
    StoryOutline,
    TemplateGenerationContext,
    OutlineGenerationContext
)
from shinkei.generation.factory import ModelFactory
from shinkei.config import settings
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

# Provider-specific temperature ranges
PROVIDER_TEMPERATURE_RANGES = {
    "openai": {"min": 0.0, "max": 2.0, "default": 0.7},
    "anthropic": {"min": 0.0, "max": 1.0, "default": 0.7},
    "ollama": {"min": 0.0, "max": 2.0, "default": 0.7},
}


class TemplateGenerationService:
    """Service for handling AI-powered story template operations."""

    def __init__(self, provider: Optional[str] = None, host: Optional[str] = None):
        """
        Initialize template generation service.

        Args:
            provider: AI provider to use (default: from settings.default_llm_provider)
            host: Base URL for the provider (used for Ollama custom hosts)
        """
        self.default_provider = provider or settings.default_llm_provider
        self.host = host
        logger.info("template_generation_service_initialized", provider=self.default_provider, host=host)

    def _get_model(self, provider: Optional[str] = None, model_name: Optional[str] = None):
        """Get model instance for the specified provider."""
        provider = provider or self.default_provider
        return ModelFactory.create(provider, model_name=model_name, host=self.host)

    def _validate_temperature(
        self,
        temperature: Optional[float],
        provider: Optional[str] = None
    ) -> float:
        """Validate and clamp temperature to provider-specific range."""
        provider = provider or self.default_provider
        ranges = PROVIDER_TEMPERATURE_RANGES.get(provider, {"min": 0.0, "max": 2.0, "default": 0.7})

        if temperature is None:
            return ranges["default"]

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
        """Build generation config with defaults and validation."""
        validated_temp = self._validate_temperature(temperature, provider)
        return GenerationConfig(
            model=model,
            temperature=validated_temp,
            max_tokens=max_tokens or 2000
        )

    async def generate_story_template(
        self,
        world_data: Dict[str, Any],
        existing_templates: List[str],
        user_prompt: Optional[str] = None,
        preferred_mode: Optional[str] = None,
        preferred_pov: Optional[str] = None,
        target_length: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> GeneratedTemplate:
        """
        Generate a custom story template based on world and user preferences.

        Args:
            world_data: World context (name, tone, backdrop, laws)
            existing_templates: List of existing template names to avoid
            user_prompt: User description of desired story type
            preferred_mode: Preferred authoring mode
            preferred_pov: Preferred point of view
            target_length: Target story length
            provider: AI provider to use
            model: Specific model to use
            temperature: Generation temperature

        Returns:
            GeneratedTemplate object
        """
        logger.info(
            "generating_story_template",
            world_name=world_data.get("name"),
            user_prompt=user_prompt,
            provider=provider or self.default_provider
        )

        # Build context
        context = TemplateGenerationContext(
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            user_prompt=user_prompt,
            preferred_mode=preferred_mode,
            preferred_pov=preferred_pov,
            target_length=target_length,
            existing_templates=existing_templates
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(
            temperature=temperature or 0.8,  # Higher for creativity
            model=model,
            max_tokens=2000,
            provider=provider
        )

        # Generate template
        try:
            template = await model_instance.generate_story_template(context, config)
            logger.info(
                "story_template_generated",
                world_name=world_data.get("name"),
                template_name=template.name
            )
            return template
        except Exception as e:
            logger.error("story_template_generation_failed", error=str(e))
            raise

    async def generate_story_outline(
        self,
        story_data: Dict[str, Any],
        world_data: Dict[str, Any],
        world_events: List[Dict[str, Any]],
        existing_characters: List[Dict[str, Any]],
        num_acts: int = 3,
        beats_per_act: int = 5,
        include_world_events: bool = True,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> StoryOutline:
        """
        Generate a story outline with act/beat structure.

        Args:
            story_data: Story context (title, synopsis, theme)
            world_data: World context (name, tone, backdrop, laws)
            world_events: List of world events to potentially incorporate
            existing_characters: List of characters for character arcs
            num_acts: Number of acts (default: 3)
            beats_per_act: Beats per act (default: 5)
            include_world_events: Whether to incorporate world events
            provider: AI provider to use
            model: Specific model to use
            temperature: Generation temperature

        Returns:
            StoryOutline object
        """
        logger.info(
            "generating_story_outline",
            story_title=story_data.get("title"),
            num_acts=num_acts,
            beats_per_act=beats_per_act,
            provider=provider or self.default_provider
        )

        # Build context
        context = OutlineGenerationContext(
            world_name=world_data.get("name", "Unknown"),
            world_tone=world_data.get("tone", ""),
            world_backdrop=world_data.get("backdrop", ""),
            world_laws=world_data.get("laws", {}),
            story_title=story_data.get("title", "Untitled"),
            story_synopsis=story_data.get("synopsis", ""),
            story_theme=story_data.get("theme"),
            num_acts=num_acts,
            beats_per_act=beats_per_act,
            world_events=world_events if include_world_events else [],
            existing_characters=existing_characters
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(
            temperature=temperature or 0.7,
            model=model,
            max_tokens=4000,  # Outlines need more tokens
            provider=provider
        )

        # Generate outline
        try:
            outline = await model_instance.generate_story_outline(context, config)
            logger.info(
                "story_outline_generated",
                story_title=story_data.get("title"),
                num_acts=len(outline.acts),
                estimated_beats=outline.estimated_beat_count
            )
            return outline
        except Exception as e:
            logger.error("story_outline_generation_failed", error=str(e))
            raise

    async def suggest_templates_for_world(
        self,
        world_data: Dict[str, Any],
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[str]:
        """
        Suggest template/genre types that fit a world.

        Args:
            world_data: World context (name, tone, backdrop, laws)
            provider: AI provider to use
            model: Specific model to use

        Returns:
            List of suggested template types (e.g., "detective noir", "epic quest")
        """
        logger.info(
            "suggesting_templates_for_world",
            world_name=world_data.get("name"),
            provider=provider or self.default_provider
        )

        # Get model and config
        model_instance = self._get_model(provider, model)
        config = self._build_config(
            temperature=0.8,  # Higher for creative suggestions
            model=model,
            max_tokens=1000,
            provider=provider
        )

        # Get suggestions
        try:
            suggestions = await model_instance.suggest_templates_for_world(
                world_name=world_data.get("name", "Unknown"),
                world_tone=world_data.get("tone", ""),
                world_backdrop=world_data.get("backdrop", ""),
                world_laws=world_data.get("laws", {}),
                config=config
            )
            logger.info(
                "template_suggestions_generated",
                world_name=world_data.get("name"),
                num_suggestions=len(suggestions)
            )
            return suggestions
        except Exception as e:
            logger.error("template_suggestions_failed", error=str(e))
            raise
