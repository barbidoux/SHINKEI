"""Tests for generation base classes and models."""
import pytest
from pydantic import ValidationError

from shinkei.generation.base import (
    GenerationRequest,
    GenerationResponse,
    NarrativeModel
)


class TestGenerationRequest:
    """Tests for GenerationRequest model."""

    def test_generation_request_minimal(self):
        """Test creating a GenerationRequest with minimal data."""
        request = GenerationRequest(prompt="Test prompt")

        assert request.prompt == "Test prompt"
        assert request.system_prompt is None
        assert request.model is None
        assert request.temperature == 0.7
        assert request.max_tokens is None
        assert request.stop_sequences == []
        assert request.metadata == {}

    def test_generation_request_full(self):
        """Test creating a GenerationRequest with all fields."""
        request = GenerationRequest(
            prompt="Full test prompt",
            system_prompt="You are a helpful assistant",
            model="gpt-4",
            temperature=0.9,
            max_tokens=1000,
            stop_sequences=["END", "STOP"],
            metadata={"user_id": "123", "session": "abc"}
        )

        assert request.prompt == "Full test prompt"
        assert request.system_prompt == "You are a helpful assistant"
        assert request.model == "gpt-4"
        assert request.temperature == 0.9
        assert request.max_tokens == 1000
        assert request.stop_sequences == ["END", "STOP"]
        assert request.metadata == {"user_id": "123", "session": "abc"}

    def test_generation_request_prompt_required(self):
        """Test that prompt is required."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationRequest()

        errors = exc_info.value.errors()
        assert any("prompt" in error.get("loc", []) for error in errors)

    def test_generation_request_temperature_validation(self):
        """Test temperature is a float."""
        request = GenerationRequest(prompt="Test", temperature=0.5)
        assert request.temperature == 0.5

        # Test with int (should be coerced to float)
        request2 = GenerationRequest(prompt="Test", temperature=1)
        assert request2.temperature == 1.0

    def test_generation_request_stop_sequences_default(self):
        """Test stop_sequences defaults to empty list."""
        request = GenerationRequest(prompt="Test")
        assert request.stop_sequences == []
        assert isinstance(request.stop_sequences, list)

    def test_generation_request_metadata_default(self):
        """Test metadata defaults to empty dict."""
        request = GenerationRequest(prompt="Test")
        assert request.metadata == {}
        assert isinstance(request.metadata, dict)

    def test_generation_request_metadata_complex(self):
        """Test metadata can hold complex structures."""
        metadata = {
            "user": {"id": 123, "name": "Test"},
            "context": ["item1", "item2"],
            "flags": {"debug": True, "verbose": False}
        }
        request = GenerationRequest(prompt="Test", metadata=metadata)
        assert request.metadata == metadata

    def test_generation_request_max_tokens_optional(self):
        """Test max_tokens can be None or int."""
        request1 = GenerationRequest(prompt="Test")
        assert request1.max_tokens is None

        request2 = GenerationRequest(prompt="Test", max_tokens=500)
        assert request2.max_tokens == 500

    def test_generation_request_model_dump(self):
        """Test serialization to dict."""
        request = GenerationRequest(
            prompt="Test",
            temperature=0.8,
            max_tokens=100
        )
        data = request.model_dump()

        assert data["prompt"] == "Test"
        assert data["temperature"] == 0.8
        assert data["max_tokens"] == 100
        assert "stop_sequences" in data
        assert "metadata" in data


class TestGenerationResponse:
    """Tests for GenerationResponse model."""

    def test_generation_response_minimal(self):
        """Test creating a GenerationResponse with minimal data."""
        response = GenerationResponse(
            content="Generated text",
            model_used="gpt-4"
        )

        assert response.content == "Generated text"
        assert response.model_used == "gpt-4"
        assert response.usage == {}
        assert response.finish_reason is None

    def test_generation_response_full(self):
        """Test creating a GenerationResponse with all fields."""
        response = GenerationResponse(
            content="Full generated text",
            model_used="claude-3-opus",
            usage={"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60},
            finish_reason="stop"
        )

        assert response.content == "Full generated text"
        assert response.model_used == "claude-3-opus"
        assert response.usage["prompt_tokens"] == 10
        assert response.usage["completion_tokens"] == 50
        assert response.usage["total_tokens"] == 60
        assert response.finish_reason == "stop"

    def test_generation_response_required_fields(self):
        """Test that content and model_used are required."""
        with pytest.raises(ValidationError) as exc_info:
            GenerationResponse()

        errors = exc_info.value.errors()
        error_fields = [error.get("loc", []) for error in errors]
        assert any("content" in fields for fields in error_fields)
        assert any("model_used" in fields for fields in error_fields)

    def test_generation_response_usage_default(self):
        """Test usage defaults to empty dict."""
        response = GenerationResponse(content="Test", model_used="gpt-4")
        assert response.usage == {}
        assert isinstance(response.usage, dict)

    def test_generation_response_finish_reason_values(self):
        """Test various finish_reason values."""
        finish_reasons = ["stop", "length", "content_filter", None]

        for reason in finish_reasons:
            response = GenerationResponse(
                content="Test",
                model_used="gpt-4",
                finish_reason=reason
            )
            assert response.finish_reason == reason

    def test_generation_response_empty_content(self):
        """Test that empty content is allowed."""
        response = GenerationResponse(content="", model_used="gpt-4")
        assert response.content == ""

    def test_generation_response_model_dump(self):
        """Test serialization to dict."""
        response = GenerationResponse(
            content="Test output",
            model_used="gpt-3.5-turbo",
            usage={"total_tokens": 100},
            finish_reason="stop"
        )
        data = response.model_dump()

        assert data["content"] == "Test output"
        assert data["model_used"] == "gpt-3.5-turbo"
        assert data["usage"]["total_tokens"] == 100
        assert data["finish_reason"] == "stop"


class TestNarrativeModel:
    """Tests for NarrativeModel abstract base class."""

    def test_narrative_model_is_abstract(self):
        """Test that NarrativeModel cannot be instantiated directly."""
        with pytest.raises(TypeError) as exc_info:
            NarrativeModel()

        assert "abstract" in str(exc_info.value).lower()

    def test_narrative_model_requires_generate(self):
        """Test that subclasses must implement generate method."""
        class IncompleteModel(NarrativeModel):
            async def stream(self, request):
                pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteModel()

        assert "generate" in str(exc_info.value).lower()

    def test_narrative_model_requires_stream(self):
        """Test that subclasses must implement stream method."""
        class IncompleteModel(NarrativeModel):
            async def generate(self, request):
                pass

        with pytest.raises(TypeError) as exc_info:
            IncompleteModel()

        assert "stream" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_narrative_model_concrete_implementation(self):
        """Test a concrete implementation of NarrativeModel."""
        class ConcreteModel(NarrativeModel):
            async def generate(self, request: GenerationRequest) -> GenerationResponse:
                return GenerationResponse(
                    content=f"Generated: {request.prompt}",
                    model_used="test-model"
                )

            async def stream(self, request: GenerationRequest):
                for word in request.prompt.split():
                    yield word

        # Should instantiate successfully
        model = ConcreteModel()

        # Test generate
        request = GenerationRequest(prompt="Test prompt")
        response = await model.generate(request)
        assert response.content == "Generated: Test prompt"
        assert response.model_used == "test-model"

        # Test stream
        chunks = []
        async for chunk in model.stream(request):
            chunks.append(chunk)
        assert chunks == ["Test", "prompt"]

    @pytest.mark.asyncio
    async def test_narrative_model_generate_signature(self):
        """Test that generate method has correct signature."""
        class TestModel(NarrativeModel):
            async def generate(self, request: GenerationRequest) -> GenerationResponse:
                return GenerationResponse(content="test", model_used="test")

            async def stream(self, request: GenerationRequest):
                yield "test"

        model = TestModel()

        # Should accept GenerationRequest
        request = GenerationRequest(prompt="Test")
        response = await model.generate(request)

        # Should return GenerationResponse
        assert isinstance(response, GenerationResponse)

    @pytest.mark.asyncio
    async def test_narrative_model_stream_signature(self):
        """Test that stream method has correct signature."""
        class TestModel(NarrativeModel):
            async def generate(self, request: GenerationRequest) -> GenerationResponse:
                return GenerationResponse(content="test", model_used="test")

            async def stream(self, request: GenerationRequest):
                yield "chunk1"
                yield "chunk2"

        model = TestModel()
        request = GenerationRequest(prompt="Test")

        # Should be an async generator
        stream = model.stream(request)
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)

        assert chunks == ["chunk1", "chunk2"]

    def test_narrative_model_inheritance(self):
        """Test that NarrativeModel can be subclassed multiple times."""
        class BaseNarrativeModel(NarrativeModel):
            async def generate(self, request: GenerationRequest) -> GenerationResponse:
                return GenerationResponse(content="base", model_used="base")

            async def stream(self, request: GenerationRequest):
                yield "base"

        class DerivedModel(BaseNarrativeModel):
            async def generate(self, request: GenerationRequest) -> GenerationResponse:
                return GenerationResponse(content="derived", model_used="derived")

        model = DerivedModel()
        assert isinstance(model, NarrativeModel)
        assert isinstance(model, BaseNarrativeModel)
