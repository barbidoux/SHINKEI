"""Tests for AI providers."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from shinkei.generation.base import GenerationRequest, GenerationResponse
from shinkei.generation.providers.openai import OpenAIModel
from shinkei.generation.providers.anthropic import AnthropicModel
from shinkei.generation.providers.ollama import OllamaModel


class TestOpenAIModel:
    """Tests for OpenAI provider."""

    @pytest.mark.asyncio
    async def test_openai_generate(self):
        """Test OpenAI generation."""
        with patch("shinkei.generation.providers.openai.AsyncOpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Test response"), finish_reason="stop")]
            mock_response.model = "gpt-4o"
            mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            model = OpenAIModel(api_key="test-key")
            request = GenerationRequest(prompt="Hello")
            response = await model.generate(request)

            assert response.content == "Test response"
            assert response.model_used == "gpt-4o"
            assert response.usage["total_tokens"] == 15

    @pytest.mark.asyncio
    async def test_openai_generate_with_system_prompt(self):
        """Test OpenAI generation with system prompt."""
        with patch("shinkei.generation.providers.openai.AsyncOpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"), finish_reason="stop")]
            mock_response.model = "gpt-4o"
            mock_response.usage = MagicMock(prompt_tokens=20, completion_tokens=10, total_tokens=30)

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            model = OpenAIModel(api_key="test-key")
            request = GenerationRequest(
                prompt="Hello",
                system_prompt="You are a helpful assistant"
            )
            response = await model.generate(request)

            assert response.content == "Response"
            assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_openai_generate_with_temperature(self):
        """Test OpenAI generation with custom temperature."""
        with patch("shinkei.generation.providers.openai.AsyncOpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"), finish_reason="stop")]
            mock_response.model = "gpt-4o"
            mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=5, total_tokens=15)

            mock_create = AsyncMock(return_value=mock_response)
            mock_client.chat.completions.create = mock_create

            model = OpenAIModel(api_key="test-key")
            request = GenerationRequest(prompt="Hello", temperature=0.9)
            await model.generate(request)

            # Verify temperature was passed to API
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["temperature"] == 0.9

    @pytest.mark.asyncio
    async def test_openai_generate_with_max_tokens(self):
        """Test OpenAI generation with max_tokens."""
        with patch("shinkei.generation.providers.openai.AsyncOpenAI") as MockClient:
            mock_client = MockClient.return_value
            mock_response = MagicMock()
            mock_response.choices = [MagicMock(message=MagicMock(content="Response"), finish_reason="length")]
            mock_response.model = "gpt-4o"
            mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=100, total_tokens=110)

            mock_create = AsyncMock(return_value=mock_response)
            mock_client.chat.completions.create = mock_create

            model = OpenAIModel(api_key="test-key")
            request = GenerationRequest(prompt="Hello", max_tokens=100)
            response = await model.generate(request)

            assert response.finish_reason == "length"
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_openai_stream(self):
        """Test OpenAI streaming."""
        with patch("shinkei.generation.providers.openai.AsyncOpenAI") as MockClient:
            mock_client = MockClient.return_value

            # Simulate streaming chunks
            async def mock_stream(*args, **kwargs):
                chunks = [
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="Hello"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content=" world"))]),
                    MagicMock(choices=[MagicMock(delta=MagicMock(content="!"))])
                ]
                for chunk in chunks:
                    yield chunk

            mock_client.chat.completions.create = mock_stream

            model = OpenAIModel(api_key="test-key")
            request = GenerationRequest(prompt="Hello")

            chunks = []
            async for chunk in model.stream(request):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]


class TestAnthropicModel:
    """Tests for Anthropic provider."""

    @pytest.mark.asyncio
    async def test_anthropic_generate(self):
        """Test Anthropic generation."""
        with patch("shinkei.generation.providers.anthropic.AsyncAnthropic") as MockClient:
            mock_client = MockClient.return_value
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Test response")]
            mock_response.model = "claude-3-5-sonnet-20240620"
            mock_response.stop_reason = "end_turn"
            mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)

            mock_client.messages.create = AsyncMock(return_value=mock_response)

            model = AnthropicModel(api_key="test-key")
            request = GenerationRequest(prompt="Hello")
            response = await model.generate(request)

            assert response.content == "Test response"
            assert response.model_used == "claude-3-5-sonnet-20240620"
            assert response.usage["input_tokens"] == 10

    @pytest.mark.asyncio
    async def test_anthropic_generate_with_system_prompt(self):
        """Test Anthropic generation with system prompt."""
        with patch("shinkei.generation.providers.anthropic.AsyncAnthropic") as MockClient:
            mock_client = MockClient.return_value
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Response")]
            mock_response.model = "claude-3-5-sonnet-20240620"
            mock_response.stop_reason = "end_turn"
            mock_response.usage = MagicMock(input_tokens=20, output_tokens=10)

            mock_create = AsyncMock(return_value=mock_response)
            mock_client.messages.create = mock_create

            model = AnthropicModel(api_key="test-key")
            request = GenerationRequest(
                prompt="Hello",
                system_prompt="You are a helpful assistant"
            )
            await model.generate(request)

            # Verify system prompt was passed
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["system"] == "You are a helpful assistant"

    @pytest.mark.asyncio
    async def test_anthropic_generate_with_max_tokens(self):
        """Test Anthropic generation with max_tokens."""
        with patch("shinkei.generation.providers.anthropic.AsyncAnthropic") as MockClient:
            mock_client = MockClient.return_value
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Response")]
            mock_response.model = "claude-3-5-sonnet-20240620"
            mock_response.stop_reason = "max_tokens"
            mock_response.usage = MagicMock(input_tokens=10, output_tokens=500)

            mock_create = AsyncMock(return_value=mock_response)
            mock_client.messages.create = mock_create

            model = AnthropicModel(api_key="test-key")
            request = GenerationRequest(prompt="Hello", max_tokens=500)
            response = await model.generate(request)

            assert response.finish_reason == "max_tokens"
            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["max_tokens"] == 500

    @pytest.mark.asyncio
    async def test_anthropic_stream(self):
        """Test Anthropic streaming."""
        with patch("shinkei.generation.providers.anthropic.AsyncAnthropic") as MockClient:
            mock_client = MockClient.return_value

            # Simulate streaming events
            async def mock_stream(*args, **kwargs):
                events = [
                    MagicMock(type="content_block_delta", delta=MagicMock(text="Hello")),
                    MagicMock(type="content_block_delta", delta=MagicMock(text=" world")),
                    MagicMock(type="message_stop")
                ]
                for event in events:
                    yield event

            mock_client.messages.create = mock_stream

            model = AnthropicModel(api_key="test-key")
            request = GenerationRequest(prompt="Hello")

            chunks = []
            async for chunk in model.stream(request):
                chunks.append(chunk)

            assert chunks == ["Hello", " world"]


class TestOllamaModel:
    """Tests for Ollama provider."""

    @pytest.mark.asyncio
    async def test_ollama_generate(self):
        """Test Ollama generation."""
        with patch("shinkei.generation.providers.ollama.AsyncClient") as MockClient:
            mock_client = MockClient.return_value
            mock_response = {
                "message": {"content": "Test response"},
                "done_reason": "stop",
                "model": "llama3",
                "prompt_eval_count": 10,
                "eval_count": 5
            }

            mock_client.chat = AsyncMock(return_value=mock_response)

            model = OllamaModel(host="http://localhost:11434")
            request = GenerationRequest(prompt="Hello")
            response = await model.generate(request)

            assert response.content == "Test response"
            assert response.model_used == "llama3"
            assert response.usage["eval_count"] == 5

    @pytest.mark.asyncio
    async def test_ollama_generate_with_custom_host(self):
        """Test Ollama with custom host."""
        with patch("shinkei.generation.providers.ollama.AsyncClient") as MockClient:
            mock_client = MockClient.return_value
            mock_response = {
                "message": {"content": "Response"},
                "done_reason": "stop",
                "model": "llama3",
                "prompt_eval_count": 10,
                "eval_count": 5
            }

            mock_client.chat = AsyncMock(return_value=mock_response)

            model = OllamaModel(host="http://custom-host:11434")
            request = GenerationRequest(prompt="Hello")
            await model.generate(request)

            # Verify client was initialized with custom host
            MockClient.assert_called_with(host="http://custom-host:11434")

    @pytest.mark.asyncio
    async def test_ollama_stream(self):
        """Test Ollama streaming."""
        with patch("shinkei.generation.providers.ollama.AsyncClient") as MockClient:
            mock_client = MockClient.return_value

            # Simulate streaming chunks
            async def mock_stream(*args, **kwargs):
                chunks = [
                    {"message": {"content": "Hello"}, "done": False},
                    {"message": {"content": " world"}, "done": False},
                    {"message": {"content": "!"}, "done": True}
                ]
                for chunk in chunks:
                    yield chunk

            mock_client.chat = mock_stream

            model = OllamaModel(host="http://localhost:11434")
            request = GenerationRequest(prompt="Hello")

            chunks = []
            async for chunk in model.stream(request):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]
