"""Factory for creating AI model instances."""
from typing import Optional
from shinkei.generation.base import NarrativeModel
from shinkei.config import settings
from shinkei.logging_config import get_logger

logger = get_logger(__name__)


class ModelFactory:
    """Factory class to instantiate AI providers."""

    @staticmethod
    def create(provider: str, api_key: Optional[str] = None, **kwargs) -> NarrativeModel:
        """
        Create a model instance for the specified provider.

        Args:
            provider: Provider name (openai, anthropic, ollama)
            api_key: Optional API key (overrides settings)
            **kwargs: Additional arguments for the provider (e.g., host for ollama)

        Returns:
            Instance of NarrativeModel

        Raises:
            ValueError: If provider is not supported or API key is missing
        """
        if provider == "openai":
            from shinkei.generation.providers.openai import OpenAIModel

            # HIGH PRIORITY FIX 2.1: Validate API key before creating provider
            final_key = api_key or settings.openai_api_key
            if not final_key:
                logger.error("openai_api_key_missing")
                raise ValueError(
                    "OpenAI API key not configured. "
                    "Set OPENAI_API_KEY environment variable or pass api_key parameter."
                )

            model = kwargs.get("model_name")
            return OpenAIModel(api_key=final_key, model=model)

        elif provider == "anthropic":
            from shinkei.generation.providers.anthropic import AnthropicModel

            # HIGH PRIORITY FIX 2.1: Validate API key before creating provider
            final_key = api_key or settings.anthropic_api_key
            if not final_key:
                logger.error("anthropic_api_key_missing")
                raise ValueError(
                    "Anthropic API key not configured. "
                    "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
                )

            model = kwargs.get("model_name")
            return AnthropicModel(api_key=final_key, model=model)

        elif provider == "ollama":
            from shinkei.generation.providers.ollama import OllamaModel
            # Ollama doesn't require an API key, just a host (defaults to localhost)
            host = kwargs.get("host") or api_key
            model = kwargs.get("model_name")

            logger.info(
                "creating_ollama_model",
                host=host or "http://localhost:11434",
                model=model
            )
            return OllamaModel(host=host, model=model)

        else:
            logger.error("unsupported_provider", provider=provider)
            raise ValueError(f"Unsupported provider: {provider}")
