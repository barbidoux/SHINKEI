"""Utility modules for the generation package.

This package provides utilities for:
- JSON and text truncation to prevent token overflow
- Retry logic with exponential backoff for AI API calls
- Metrics and observability for AI operations
"""
from shinkei.generation.utils.json_truncation import (
    smart_truncate_json,
    smart_truncate_list,
    smart_truncate_metadata,
    truncate_text_for_extraction,
    MAX_TEXT_LENGTH,
    MAX_BACKDROP_LENGTH,
    MAX_LAWS_LENGTH,
    MAX_METADATA_LENGTH
)
from shinkei.generation.utils.retry import (
    async_retry_with_backoff,
    retry_on_error,
    retry_ai_call,
    is_rate_limit_error,
    DEFAULT_MAX_RETRIES,
    DEFAULT_BASE_DELAY,
    DEFAULT_MAX_DELAY
)
from shinkei.generation.utils.metrics import (
    AICallMetrics,
    MetricsCollector,
    get_metrics_collector,
    track_ai_call,
    timed_ai_operation,
    extract_token_usage
)

__all__ = [
    # JSON and text truncation
    "smart_truncate_json",
    "smart_truncate_list",
    "smart_truncate_metadata",
    "truncate_text_for_extraction",
    "MAX_TEXT_LENGTH",
    "MAX_BACKDROP_LENGTH",
    "MAX_LAWS_LENGTH",
    "MAX_METADATA_LENGTH",
    # Retry utilities
    "async_retry_with_backoff",
    "retry_on_error",
    "retry_ai_call",
    "is_rate_limit_error",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_BASE_DELAY",
    "DEFAULT_MAX_DELAY",
    # Metrics and observability
    "AICallMetrics",
    "MetricsCollector",
    "get_metrics_collector",
    "track_ai_call",
    "timed_ai_operation",
    "extract_token_usage",
]
