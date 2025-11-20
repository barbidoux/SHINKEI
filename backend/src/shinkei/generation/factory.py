"""Factory for creating AI model instances."""
from typing import Optional
from shinkei.generation.base import NarrativeModel
from shinkei.config import settings


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
            ValueError: If provider is not supported
        """
        if provider == "openai":
            from shinkei.generation.providers.openai import OpenAIModel
            model = kwargs.get("model_name")
            return OpenAIModel(api_key=api_key or settings.openai_api_key, model=model)
        
        elif provider == "anthropic":
            from shinkei.generation.providers.anthropic import AnthropicModel
            model = kwargs.get("model_name")
            return AnthropicModel(api_key=api_key or settings.anthropic_api_key, model=model)
            
        elif provider == "ollama":
            from shinkei.generation.providers.ollama import OllamaModel
            # Pass host from kwargs if available, otherwise use api_key as fallback or default
            host = kwargs.get("host") or api_key
            model = kwargs.get("model_name")
            return OllamaModel(host=host, model=model)
            
        else:
            raise ValueError(f"Unsupported provider: {provider}")
