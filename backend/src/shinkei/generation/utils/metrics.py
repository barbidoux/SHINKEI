"""Metrics and observability utilities for AI generation operations.

Provides timing, token tracking, and success rate monitoring for AI provider calls.
"""
import time
import asyncio
import functools
from typing import Dict, Any, Optional, Callable, TypeVar
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections import defaultdict
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')


@dataclass
class AICallMetrics:
    """Metrics for a single AI call."""
    provider: str
    operation: str
    model: str
    latency_ms: float
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    success: bool = True
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Singleton collector for AI operation metrics."""

    _instance: Optional['MetricsCollector'] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> 'MetricsCollector':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        # Metrics storage
        self._call_counts: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._total_latency_ms: Dict[str, float] = defaultdict(float)
        self._total_tokens: Dict[str, int] = defaultdict(int)
        self._recent_calls: list = []
        self._max_recent_calls = 100

    def record(self, metrics: AICallMetrics) -> None:
        """Record metrics for an AI call."""
        key = f"{metrics.provider}:{metrics.operation}"

        self._call_counts[key] += 1
        self._total_latency_ms[key] += metrics.latency_ms
        self._total_tokens[key] += metrics.total_tokens

        if not metrics.success:
            error_key = f"{key}:{metrics.error_type or 'unknown'}"
            self._error_counts[error_key] += 1

        # Store recent calls for debugging
        self._recent_calls.append(metrics)
        if len(self._recent_calls) > self._max_recent_calls:
            self._recent_calls.pop(0)

        # Log the metrics
        log_data = {
            "provider": metrics.provider,
            "operation": metrics.operation,
            "model": metrics.model,
            "latency_ms": round(metrics.latency_ms, 2),
            "total_tokens": metrics.total_tokens,
            "success": metrics.success
        }

        if metrics.success:
            logger.info("ai_call_completed", **log_data)
        else:
            log_data["error_type"] = metrics.error_type
            log_data["error_message"] = metrics.error_message[:200] if metrics.error_message else None
            logger.warning("ai_call_failed", **log_data)

    def get_stats(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated statistics."""
        stats = {
            "call_counts": dict(self._call_counts),
            "error_counts": dict(self._error_counts),
            "average_latency_ms": {},
            "total_tokens": dict(self._total_tokens)
        }

        # Calculate averages
        for key, count in self._call_counts.items():
            if count > 0:
                stats["average_latency_ms"][key] = round(
                    self._total_latency_ms[key] / count, 2
                )

        # Filter by provider if specified
        if provider:
            stats = {
                k: {
                    sub_k: v for sub_k, v in d.items()
                    if sub_k.startswith(f"{provider}:")
                } if isinstance(d, dict) else d
                for k, d in stats.items()
            }

        return stats

    def get_recent_calls(self, limit: int = 10) -> list:
        """Get recent call metrics for debugging."""
        return self._recent_calls[-limit:]

    def reset(self) -> None:
        """Reset all metrics (useful for testing)."""
        self._call_counts.clear()
        self._error_counts.clear()
        self._total_latency_ms.clear()
        self._total_tokens.clear()
        self._recent_calls.clear()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


@asynccontextmanager
async def track_ai_call(
    provider: str,
    operation: str,
    model: str,
    **extra_metadata
):
    """
    Context manager to track AI call metrics.

    Usage:
        async with track_ai_call("openai", "extract_entities", "gpt-4") as tracker:
            result = await model.extract_entities(...)
            tracker.set_tokens(input=100, output=50)

    Args:
        provider: AI provider name
        operation: Operation being performed
        model: Model being used
        **extra_metadata: Additional metadata to record
    """
    start_time = time.perf_counter()
    tracker = _CallTracker(provider, operation, model, extra_metadata)

    try:
        yield tracker
        tracker.success = True
    except Exception as e:
        tracker.success = False
        tracker.error_type = type(e).__name__
        tracker.error_message = str(e)
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        metrics = AICallMetrics(
            provider=provider,
            operation=operation,
            model=model,
            latency_ms=elapsed_ms,
            input_tokens=tracker.input_tokens,
            output_tokens=tracker.output_tokens,
            total_tokens=tracker.input_tokens + tracker.output_tokens,
            success=tracker.success,
            error_type=tracker.error_type,
            error_message=tracker.error_message,
            metadata=tracker.metadata
        )

        get_metrics_collector().record(metrics)


class _CallTracker:
    """Helper class for tracking call metrics within context manager."""

    def __init__(
        self,
        provider: str,
        operation: str,
        model: str,
        metadata: Dict[str, Any]
    ):
        self.provider = provider
        self.operation = operation
        self.model = model
        self.metadata = metadata
        self.input_tokens = 0
        self.output_tokens = 0
        self.success = True
        self.error_type: Optional[str] = None
        self.error_message: Optional[str] = None

    def set_tokens(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: Optional[int] = None
    ) -> None:
        """Set token counts from response."""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        if total_tokens is not None and input_tokens == 0 and output_tokens == 0:
            # If only total is provided, use it as output estimate
            self.output_tokens = total_tokens

    def add_metadata(self, key: str, value: Any) -> None:
        """Add additional metadata."""
        self.metadata[key] = value


def timed_ai_operation(
    provider: str,
    operation: str
) -> Callable:
    """
    Decorator to automatically track metrics for AI operations.

    Usage:
        @timed_ai_operation("openai", "extract_entities")
        async def extract_entities(self, context, config):
            ...

    Args:
        provider: AI provider name
        operation: Operation name

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Try to get model from config argument
            model = "unknown"
            for arg in args:
                if hasattr(arg, 'model') and arg.model:
                    model = arg.model
                    break
            for key in ['config', 'generation_config']:
                if key in kwargs and hasattr(kwargs[key], 'model'):
                    model = kwargs[key].model or model
                    break

            async with track_ai_call(provider, operation, model):
                return await func(*args, **kwargs)

        return wrapper
    return decorator


def extract_token_usage(response: Any, provider: str) -> Dict[str, int]:
    """
    Extract token usage from provider response.

    Args:
        response: Provider response object
        provider: Provider name for format detection

    Returns:
        Dict with input_tokens, output_tokens, total_tokens
    """
    usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    if provider == "openai":
        if hasattr(response, 'usage') and response.usage:
            usage["input_tokens"] = getattr(response.usage, 'prompt_tokens', 0)
            usage["output_tokens"] = getattr(response.usage, 'completion_tokens', 0)
            usage["total_tokens"] = getattr(response.usage, 'total_tokens', 0)

    elif provider == "anthropic":
        if hasattr(response, 'usage'):
            usage["input_tokens"] = getattr(response.usage, 'input_tokens', 0)
            usage["output_tokens"] = getattr(response.usage, 'output_tokens', 0)
            usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]

    elif provider == "ollama":
        if isinstance(response, dict):
            usage["input_tokens"] = response.get('prompt_eval_count', 0)
            usage["output_tokens"] = response.get('eval_count', 0)
            usage["total_tokens"] = usage["input_tokens"] + usage["output_tokens"]

    return usage
