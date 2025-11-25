"""Service layer for AI generation."""
from typing import Optional, Dict, Any
from shinkei.generation.base import GenerationRequest, GenerationResponse
from shinkei.generation.factory import ModelFactory
from shinkei.generation.prompts import PROMPTS
from shinkei.config import settings
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class GenerationService:
    """Service for handling AI generation requests."""

    def __init__(self, provider: Optional[str] = None):
        """
        Initialize generation service.

        Args:
            provider: AI provider to use (default: from settings.default_llm_provider)
        """
        self.default_provider = provider or settings.default_llm_provider
        # Note: model instance is created per-request in generate_from_template
        # to allow user_settings overrides

    async def generate_from_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        model_override: Optional[str] = None,
        temperature: float = 0.7,
        user_settings: Optional[Dict[str, Any]] = None
    ) -> GenerationResponse:
        """
        Generate text using a prompt template.
        
        Args:
            template_name: Name of the prompt template
            context: Dictionary of context variables for the template
            model_override: Optional model name override
            temperature: Temperature for generation
            user_settings: Optional user settings to override defaults
            
        Returns:
            GenerationResponse object
        """
        if template_name not in PROMPTS:
            raise ValueError(f"Unknown prompt template: {template_name}")
            
        prompt_template = PROMPTS[template_name]
        try:
            prompt = prompt_template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing context variable: {e}")
            
        # Determine provider and model from settings if available
        provider = self.default_provider
        model = model_override
        base_url = None
        
        if user_settings:
            if "llm_provider" in user_settings:
                provider = user_settings["llm_provider"]
            if "llm_model" in user_settings and not model:
                model = user_settings["llm_model"]
            if "llm_base_url" in user_settings:
                base_url = user_settings["llm_base_url"]
        
        # Use the configured provider/model
        model_instance = ModelFactory.create(provider, host=base_url)

        # Create generation request
        request = GenerationRequest(
            prompt=prompt,
            model=model,
            temperature=temperature
        )

        logger.info("generation_started", template=template_name, provider=provider, model=model)
        response = await model_instance.generate(request)
        logger.info("generation_completed", template=template_name, provider=provider)

        return response
