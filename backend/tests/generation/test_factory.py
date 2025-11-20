"""Tests for ModelFactory."""
import pytest
from unittest.mock import patch, MagicMock
from shinkei.generation.factory import ModelFactory
from shinkei.generation.base import NarrativeModel


class TestModelFactoryCreate:
    """Tests for ModelFactory.create method."""

    def test_create_openai_model(self):
        """Test creating OpenAI model."""
        with patch("shinkei.generation.providers.openai.OpenAIModel") as MockOpenAI:
            mock_instance = MagicMock(spec=NarrativeModel)
            MockOpenAI.return_value = mock_instance

            model = ModelFactory.create("openai", api_key="test-key")

            assert model == mock_instance
            MockOpenAI.assert_called_once_with(api_key="test-key")

    def test_create_anthropic_model(self):
        """Test creating Anthropic model."""
        with patch("shinkei.generation.providers.anthropic.AnthropicModel") as MockAnthropic:
            mock_instance = MagicMock(spec=NarrativeModel)
            MockAnthropic.return_value = mock_instance

            model = ModelFactory.create("anthropic", api_key="test-key")

            assert model == mock_instance
            MockAnthropic.assert_called_once_with(api_key="test-key")

    def test_create_ollama_model_with_api_key(self):
        """Test creating Ollama model using api_key parameter."""
        with patch("shinkei.generation.providers.ollama.OllamaModel") as MockOllama:
            mock_instance = MagicMock(spec=NarrativeModel)
            MockOllama.return_value = mock_instance

            model = ModelFactory.create("ollama", api_key="http://localhost:11434")

            assert model == mock_instance
            MockOllama.assert_called_once_with(host="http://localhost:11434")

    def test_create_ollama_model_with_host_kwarg(self):
        """Test creating Ollama model using host kwarg."""
        with patch("shinkei.generation.providers.ollama.OllamaModel") as MockOllama:
            mock_instance = MagicMock(spec=NarrativeModel)
            MockOllama.return_value = mock_instance

            model = ModelFactory.create("ollama", host="http://custom:11434")

            assert model == mock_instance
            MockOllama.assert_called_once_with(host="http://custom:11434")

    def test_create_unsupported_provider(self):
        """Test creating unsupported provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider: unknown"):
            ModelFactory.create("unknown")

    def test_create_with_empty_provider(self):
        """Test creating with empty provider string raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider: "):
            ModelFactory.create("")

    def test_create_openai_without_api_key_uses_settings(self):
        """Test creating OpenAI without api_key uses settings."""
        with patch("shinkei.generation.providers.openai.OpenAIModel") as MockOpenAI, \
             patch("shinkei.generation.factory.settings") as mock_settings:
            mock_settings.openai_api_key = "settings-key"
            mock_instance = MagicMock(spec=NarrativeModel)
            MockOpenAI.return_value = mock_instance

            model = ModelFactory.create("openai")

            assert model == mock_instance
            MockOpenAI.assert_called_once_with(api_key="settings-key")

    def test_create_anthropic_without_api_key_uses_settings(self):
        """Test creating Anthropic without api_key uses settings."""
        with patch("shinkei.generation.providers.anthropic.AnthropicModel") as MockAnthropic, \
             patch("shinkei.generation.factory.settings") as mock_settings:
            mock_settings.anthropic_api_key = "settings-key"
            mock_instance = MagicMock(spec=NarrativeModel)
            MockAnthropic.return_value = mock_instance

            model = ModelFactory.create("anthropic")

            assert model == mock_instance
            MockAnthropic.assert_called_once_with(api_key="settings-key")


class TestModelFactoryCaseInsensitivity:
    """Tests for provider name case handling."""

    def test_provider_names_are_case_sensitive(self):
        """Test that provider names are case-sensitive."""
        # The factory expects lowercase provider names
        with pytest.raises(ValueError, match="Unsupported provider: OpenAI"):
            ModelFactory.create("OpenAI", api_key="test")

    def test_provider_names_reject_uppercase(self):
        """Test that uppercase provider names are rejected."""
        with pytest.raises(ValueError, match="Unsupported provider: ANTHROPIC"):
            ModelFactory.create("ANTHROPIC", api_key="test")
