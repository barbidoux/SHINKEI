"""Tests for GenerationService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from shinkei.generation.service import GenerationService
from shinkei.generation.base import GenerationResponse


class TestGenerationServiceInit:
    """Tests for GenerationService initialization."""

    def test_service_init_with_default_provider(self):
        """Test service initialization with default provider."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            MockFactory.create.return_value = mock_model

            service = GenerationService()

            assert service.provider == "openai"
            MockFactory.create.assert_called_once_with("openai")

    def test_service_init_with_custom_provider(self):
        """Test service initialization with custom provider."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="anthropic")

            assert service.provider == "anthropic"
            MockFactory.create.assert_called_once_with("anthropic")


class TestGenerationServiceGenerateFromTemplate:
    """Tests for GenerationService.generate_from_template method."""

    @pytest.mark.asyncio
    async def test_generate_from_template(self):
        """Test generating from template."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            mock_response = GenerationResponse(
                content="Generated content",
                model_used="test-model"
            )
            mock_model.generate = AsyncMock(return_value=mock_response)
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            context = {"theme": "Sci-Fi"}
            response = await service.generate_from_template("generate_story_ideas", context)

            assert response.content == "Generated content"
            mock_model.generate.assert_called_once()

            # Verify prompt formatting
            call_args = mock_model.generate.call_args
            request = call_args[0][0]
            assert "Sci-Fi" in request.prompt

    @pytest.mark.asyncio
    async def test_generate_from_template_with_custom_temperature(self):
        """Test generating from template with custom temperature."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            mock_response = GenerationResponse(content="Response", model_used="test-model")
            mock_model.generate = AsyncMock(return_value=mock_response)
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            context = {"theme": "Fantasy"}
            response = await service.generate_from_template(
                "generate_story_ideas",
                context,
                temperature=0.9
            )

            assert response.content == "Response"

    @pytest.mark.asyncio
    async def test_generate_from_template_missing_context(self):
        """Test generating from template with missing context."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            context = {} # Missing theme

            with pytest.raises(ValueError, match="Missing context variable"):
                await service.generate_from_template("generate_story_ideas", context)

    @pytest.mark.asyncio
    async def test_generate_from_template_unknown_template(self):
        """Test generating from unknown template."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            with pytest.raises(ValueError, match="Unknown prompt template"):
                await service.generate_from_template("unknown_template", {})

    @pytest.mark.asyncio
    async def test_generate_from_template_with_user_settings_provider(self):
        """Test generating with user settings overriding provider."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            mock_response = GenerationResponse(content="Response", model_used="test-model")
            mock_model.generate = AsyncMock(return_value=mock_response)
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            context = {"theme": "Mystery"}
            user_settings = {"llm_provider": "anthropic"}

            response = await service.generate_from_template(
                "generate_story_ideas",
                context,
                user_settings=user_settings
            )

            # Verify ModelFactory was called with anthropic provider
            assert MockFactory.create.call_count == 2  # Once in __init__, once in method
            last_call_args = MockFactory.create.call_args_list[1]
            assert last_call_args[0][0] == "anthropic"

    @pytest.mark.asyncio
    async def test_generate_from_template_with_user_settings_model(self):
        """Test generating with user settings specifying model."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            mock_response = GenerationResponse(content="Response", model_used="custom-model")
            mock_model.generate = AsyncMock(return_value=mock_response)
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            context = {"theme": "Horror"}
            user_settings = {"llm_model": "gpt-4o"}

            response = await service.generate_from_template(
                "generate_story_ideas",
                context,
                user_settings=user_settings
            )

            assert response.model_used == "custom-model"

    @pytest.mark.asyncio
    async def test_generate_from_template_with_user_settings_base_url(self):
        """Test generating with user settings specifying base URL."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            mock_response = GenerationResponse(content="Response", model_used="test-model")
            mock_model.generate = AsyncMock(return_value=mock_response)
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="ollama")

            context = {"theme": "Adventure"}
            user_settings = {"llm_base_url": "http://custom:11434"}

            response = await service.generate_from_template(
                "generate_story_ideas",
                context,
                user_settings=user_settings
            )

            # Verify host kwarg was passed
            last_call_kwargs = MockFactory.create.call_args_list[1][1]
            assert last_call_kwargs["host"] == "http://custom:11434"

    @pytest.mark.asyncio
    async def test_generate_from_template_with_model_override(self):
        """Test generating with model override parameter."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            mock_response = GenerationResponse(content="Response", model_used="override-model")
            mock_model.generate = AsyncMock(return_value=mock_response)
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            context = {"theme": "Romance"}
            response = await service.generate_from_template(
                "generate_story_ideas",
                context,
                model_override="gpt-4o-mini"
            )

            assert response.model_used == "override-model"

    @pytest.mark.asyncio
    async def test_generate_from_template_expand_beat(self):
        """Test generating from expand_beat template."""
        with patch("shinkei.generation.service.ModelFactory") as MockFactory:
            mock_model = MagicMock()
            mock_response = GenerationResponse(
                content="Expanded scene content",
                model_used="test-model"
            )
            mock_model.generate = AsyncMock(return_value=mock_response)
            MockFactory.create.return_value = mock_model

            service = GenerationService(provider="openai")

            context = {
                "world_name": "Cyber Tokyo",
                "story_title": "Neon Dreams",
                "beat_content": "The hero arrives"
            }
            response = await service.generate_from_template("expand_beat", context)

            assert response.content == "Expanded scene content"
            call_args = mock_model.generate.call_args
            request = call_args[0][0]
            assert "Cyber Tokyo" in request.prompt
            assert "Neon Dreams" in request.prompt
