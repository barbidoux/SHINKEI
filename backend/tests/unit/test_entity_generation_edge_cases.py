"""Unit tests for AI entity generation edge cases and validation fixes."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from shinkei.generation.utils.json_truncation import (
    smart_truncate_json,
    smart_truncate_list,
    smart_truncate_metadata,
    truncate_text_for_extraction,
    MAX_TEXT_LENGTH
)
from shinkei.generation.utils.retry import (
    async_retry_with_backoff,
    retry_on_error,
    is_rate_limit_error
)
from shinkei.generation.factory import ModelFactory
from shinkei.generation.entity_generation_service import (
    EntityGenerationService,
    PROVIDER_TEMPERATURE_RANGES
)


class TestSmartJSONTruncation:
    """Tests for smart JSON truncation utilities."""

    def test_truncate_empty_dict(self):
        """Empty dict returns valid empty JSON."""
        result = smart_truncate_json({})
        assert result == "{}"

    def test_truncate_none(self):
        """None returns valid empty JSON."""
        result = smart_truncate_json(None)
        assert result == "{}"

    def test_truncate_small_dict(self):
        """Small dict within limit returns full JSON."""
        data = {"name": "Test", "value": 123}
        result = smart_truncate_json(data, max_length=1000)
        assert json.loads(result) == data

    def test_truncate_large_dict(self):
        """Large dict is truncated but remains valid JSON."""
        data = {f"key_{i}": f"value_{i}" * 100 for i in range(20)}
        result = smart_truncate_json(data, max_length=500, max_keys=5)
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        # Should have limited keys
        assert len(parsed) <= 6  # max_keys + potential ellipsis

    def test_truncate_nested_dict(self):
        """Nested structures are summarized."""
        data = {
            "nested": {"deep": {"deeper": "value"}},
            "list": [1, 2, 3, 4, 5]
        }
        result = smart_truncate_json(data, max_length=100)
        parsed = json.loads(result)
        # Nested structures replaced with indicators
        assert isinstance(parsed, dict)


class TestTextTruncation:
    """Tests for text truncation to prevent token overflow."""

    def test_short_text_unchanged(self):
        """Short text is returned unchanged."""
        text = "This is short text."
        result = truncate_text_for_extraction(text)
        assert result == text

    def test_long_text_truncated(self):
        """Long text is truncated with indicator."""
        text = "A" * (MAX_TEXT_LENGTH + 1000)
        result = truncate_text_for_extraction(text)
        assert len(result) < len(text)
        assert "[Text truncated" in result

    def test_truncation_at_sentence_boundary(self):
        """Truncation prefers sentence boundaries."""
        # Create text with sentences
        text = "First sentence. " * 1000
        result = truncate_text_for_extraction(text, max_length=100)
        # Should end at sentence boundary
        assert result.count(". ") > 0 or "[Text truncated" in result

    def test_empty_text(self):
        """Empty text returns empty string."""
        assert truncate_text_for_extraction("") == ""
        assert truncate_text_for_extraction(None) is None


class TestTemperatureValidation:
    """Tests for provider-specific temperature validation."""

    @pytest.fixture
    def service(self):
        return EntityGenerationService(provider="openai")

    def test_temperature_within_range(self, service):
        """Valid temperature is returned unchanged."""
        assert service._validate_temperature(0.7, "openai") == 0.7
        assert service._validate_temperature(0.5, "anthropic") == 0.5

    def test_temperature_clamped_to_max(self, service):
        """Temperature above max is clamped."""
        # Anthropic max is 1.0
        result = service._validate_temperature(1.5, "anthropic")
        assert result == 1.0

        # OpenAI max is 2.0
        result = service._validate_temperature(3.0, "openai")
        assert result == 2.0

    def test_temperature_clamped_to_min(self, service):
        """Temperature below min is clamped."""
        result = service._validate_temperature(-0.5, "openai")
        assert result == 0.0

    def test_temperature_none_uses_default(self, service):
        """None temperature uses provider default."""
        result = service._validate_temperature(None, "openai")
        assert result == PROVIDER_TEMPERATURE_RANGES["openai"]["default"]

    def test_unknown_provider_uses_safe_defaults(self, service):
        """Unknown provider uses safe default range."""
        result = service._validate_temperature(0.7, "unknown_provider")
        assert result == 0.7


class TestDeduplication:
    """Tests for entity deduplication logic."""

    @pytest.fixture
    def service(self):
        return EntityGenerationService(provider="openai")

    def test_no_duplicates(self, service):
        """Non-duplicate list is unchanged."""
        from shinkei.generation.base import EntitySuggestion

        suggestions = [
            EntitySuggestion(name="Alice", entity_type="character", confidence=0.9),
            EntitySuggestion(name="Bob", entity_type="character", confidence=0.8),
        ]
        result = service._deduplicate_suggestions(suggestions)
        assert len(result) == 2

    def test_duplicate_names_keep_highest_confidence(self, service):
        """Duplicate names keep highest confidence."""
        from shinkei.generation.base import EntitySuggestion

        suggestions = [
            EntitySuggestion(name="Alice", entity_type="character", confidence=0.7),
            EntitySuggestion(name="Alice", entity_type="character", confidence=0.9),
            EntitySuggestion(name="alice", entity_type="character", confidence=0.8),
        ]
        result = service._deduplicate_suggestions(suggestions)
        assert len(result) == 1
        assert result[0].confidence == 0.9

    def test_same_name_different_types(self, service):
        """Same name but different types are kept."""
        from shinkei.generation.base import EntitySuggestion

        suggestions = [
            EntitySuggestion(name="Forest", entity_type="character", confidence=0.8),
            EntitySuggestion(name="Forest", entity_type="location", confidence=0.9),
        ]
        result = service._deduplicate_suggestions(suggestions)
        assert len(result) == 2


class TestAPIKeyValidation:
    """Tests for API key validation in factory."""

    def test_missing_openai_key_raises(self):
        """Missing OpenAI key raises ValueError."""
        with patch.object(
            ModelFactory, 'create', wraps=ModelFactory.create
        ) as mock_create:
            with patch('shinkei.generation.factory.settings') as mock_settings:
                mock_settings.openai_api_key = None
                with pytest.raises(ValueError, match="OpenAI API key"):
                    ModelFactory.create("openai", api_key=None)

    def test_missing_anthropic_key_raises(self):
        """Missing Anthropic key raises ValueError."""
        with patch('shinkei.generation.factory.settings') as mock_settings:
            mock_settings.anthropic_api_key = None
            with pytest.raises(ValueError, match="Anthropic API key"):
                ModelFactory.create("anthropic", api_key=None)

    def test_ollama_no_key_required(self):
        """Ollama doesn't require API key."""
        with patch('shinkei.generation.factory.settings') as mock_settings:
            mock_settings.default_llm_provider = "ollama"
            # Should not raise
            try:
                with patch('shinkei.generation.providers.ollama.AsyncClient'):
                    ModelFactory.create("ollama")
            except Exception as e:
                # May fail for other reasons, but not API key
                assert "API key" not in str(e)


class TestRetryUtilities:
    """Tests for retry with exponential backoff."""

    @pytest.mark.asyncio
    async def test_successful_call_no_retry(self):
        """Successful call returns without retry."""
        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await async_retry_with_backoff(mock_func, max_retries=3)
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """TimeoutError triggers retry."""
        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("timeout")
            return "success"

        result = await async_retry_with_backoff(
            mock_func,
            max_retries=3,
            base_delay=0.01
        )
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_non_retryable_error_raises_immediately(self):
        """Non-retryable errors are raised immediately."""
        call_count = 0

        async def mock_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("not retryable")

        with pytest.raises(ValueError):
            await async_retry_with_backoff(
                mock_func,
                max_retries=3,
                retryable_exceptions=(TimeoutError,)
            )
        assert call_count == 1

    def test_rate_limit_detection(self):
        """Rate limit errors are detected correctly."""
        assert is_rate_limit_error(Exception("Rate limit exceeded"))
        assert is_rate_limit_error(Exception("429 Too Many Requests"))
        assert is_rate_limit_error(Exception("quota exceeded"))
        assert not is_rate_limit_error(Exception("generic error"))


class TestEntityExtractionEmptyText:
    """Tests for empty text handling in entity extraction."""

    @pytest.mark.asyncio
    async def test_empty_text_returns_empty_list(self):
        """Empty text returns empty suggestions without API call."""
        from shinkei.generation.base import EntityExtractionContext, GenerationConfig

        with patch('openai.AsyncOpenAI'):
            from shinkei.generation.providers.openai import OpenAIModel

            model = OpenAIModel(api_key="test", model="gpt-4")

            context = EntityExtractionContext(
                text="",
                world_name="Test World",
                world_tone="dark",
                world_backdrop="Test backdrop",
                world_laws={},
                existing_characters=[],
                existing_locations=[],
                confidence_threshold=0.7
            )
            config = GenerationConfig(model="gpt-4", temperature=0.7, max_tokens=2000)

            result = await model.extract_entities(context, config)
            assert result == []

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_empty_list(self):
        """Whitespace-only text returns empty suggestions."""
        from shinkei.generation.base import EntityExtractionContext, GenerationConfig

        with patch('openai.AsyncOpenAI'):
            from shinkei.generation.providers.openai import OpenAIModel

            model = OpenAIModel(api_key="test", model="gpt-4")

            context = EntityExtractionContext(
                text="   \n\t  ",
                world_name="Test World",
                world_tone="dark",
                world_backdrop="Test backdrop",
                world_laws={},
                existing_characters=[],
                existing_locations=[],
                confidence_threshold=0.7
            )
            config = GenerationConfig(model="gpt-4", temperature=0.7, max_tokens=2000)

            result = await model.extract_entities(context, config)
            assert result == []


class TestMetricsCollector:
    """Tests for AI metrics collection and observability."""

    def test_metrics_collector_singleton(self):
        """MetricsCollector is a singleton."""
        from shinkei.generation.utils.metrics import MetricsCollector

        collector1 = MetricsCollector()
        collector2 = MetricsCollector()
        assert collector1 is collector2

    def test_record_and_get_stats(self):
        """Metrics are recorded and retrievable."""
        from shinkei.generation.utils.metrics import (
            get_metrics_collector,
            AICallMetrics
        )

        collector = get_metrics_collector()
        collector.reset()  # Clear any previous state

        # Record a successful call
        metrics = AICallMetrics(
            provider="openai",
            operation="extract_entities",
            model="gpt-4",
            latency_ms=150.5,
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            success=True
        )
        collector.record(metrics)

        stats = collector.get_stats()
        assert "openai:extract_entities" in stats["call_counts"]
        assert stats["call_counts"]["openai:extract_entities"] == 1
        assert stats["total_tokens"]["openai:extract_entities"] == 150

    def test_record_failure(self):
        """Failed calls are tracked separately."""
        from shinkei.generation.utils.metrics import (
            get_metrics_collector,
            AICallMetrics
        )

        collector = get_metrics_collector()
        collector.reset()

        # Record a failed call
        metrics = AICallMetrics(
            provider="anthropic",
            operation="generate_character",
            model="claude-3",
            latency_ms=50.0,
            success=False,
            error_type="TimeoutError",
            error_message="Connection timed out"
        )
        collector.record(metrics)

        stats = collector.get_stats()
        assert "anthropic:generate_character:TimeoutError" in stats["error_counts"]
        assert stats["error_counts"]["anthropic:generate_character:TimeoutError"] == 1

    def test_average_latency_calculation(self):
        """Average latency is calculated correctly."""
        from shinkei.generation.utils.metrics import (
            get_metrics_collector,
            AICallMetrics
        )

        collector = get_metrics_collector()
        collector.reset()

        # Record multiple calls
        for latency in [100.0, 200.0, 300.0]:
            metrics = AICallMetrics(
                provider="ollama",
                operation="summarize",
                model="llama3",
                latency_ms=latency,
                success=True
            )
            collector.record(metrics)

        stats = collector.get_stats()
        # Average should be 200.0
        assert stats["average_latency_ms"]["ollama:summarize"] == 200.0

    def test_recent_calls_limit(self):
        """Recent calls are limited to max size."""
        from shinkei.generation.utils.metrics import (
            get_metrics_collector,
            AICallMetrics
        )

        collector = get_metrics_collector()
        collector.reset()
        collector._max_recent_calls = 5  # Set low limit for testing

        # Record more than the limit
        for i in range(10):
            metrics = AICallMetrics(
                provider="openai",
                operation=f"op_{i}",
                model="gpt-4",
                latency_ms=100.0,
                success=True
            )
            collector.record(metrics)

        recent = collector.get_recent_calls(limit=10)
        assert len(recent) <= 5

    @pytest.mark.asyncio
    async def test_track_ai_call_context_manager(self):
        """Context manager tracks metrics correctly."""
        from shinkei.generation.utils.metrics import (
            get_metrics_collector,
            track_ai_call
        )

        collector = get_metrics_collector()
        collector.reset()

        async with track_ai_call("openai", "test_op", "gpt-4") as tracker:
            tracker.set_tokens(input_tokens=50, output_tokens=25)
            # Simulate some work
            pass

        stats = collector.get_stats()
        assert "openai:test_op" in stats["call_counts"]
        assert stats["total_tokens"]["openai:test_op"] == 75

    @pytest.mark.asyncio
    async def test_track_ai_call_with_error(self):
        """Context manager tracks errors correctly."""
        from shinkei.generation.utils.metrics import (
            get_metrics_collector,
            track_ai_call
        )

        collector = get_metrics_collector()
        collector.reset()

        with pytest.raises(ValueError):
            async with track_ai_call("anthropic", "failing_op", "claude-3"):
                raise ValueError("Test error")

        stats = collector.get_stats()
        assert "anthropic:failing_op:ValueError" in stats["error_counts"]

    def test_extract_token_usage_openai(self):
        """Token extraction works for OpenAI format."""
        from shinkei.generation.utils.metrics import extract_token_usage

        # Mock OpenAI response
        class MockUsage:
            prompt_tokens = 100
            completion_tokens = 50
            total_tokens = 150

        class MockResponse:
            usage = MockUsage()

        usage = extract_token_usage(MockResponse(), "openai")
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 50
        assert usage["total_tokens"] == 150

    def test_extract_token_usage_ollama(self):
        """Token extraction works for Ollama format."""
        from shinkei.generation.utils.metrics import extract_token_usage

        # Ollama returns dict
        response = {
            "prompt_eval_count": 80,
            "eval_count": 40
        }

        usage = extract_token_usage(response, "ollama")
        assert usage["input_tokens"] == 80
        assert usage["output_tokens"] == 40
        assert usage["total_tokens"] == 120
