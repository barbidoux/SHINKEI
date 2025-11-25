"""Retry utilities for AI provider operations with exponential backoff."""
import asyncio
import functools
from typing import TypeVar, Callable, Any, Optional, Type, Tuple
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

# Default retry settings
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 10.0  # seconds

# Errors that are worth retrying
RETRYABLE_ERRORS: Tuple[Type[Exception], ...] = (
    TimeoutError,
    ConnectionError,
    asyncio.TimeoutError,
)


async def async_retry_with_backoff(
    func: Callable[..., Any],
    *args,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_exceptions: Tuple[Type[Exception], ...] = RETRYABLE_ERRORS,
    **kwargs
) -> Any:
    """
    MEDIUM PRIORITY FIX 3.2: Retry an async function with exponential backoff.

    Args:
        func: Async function to call
        *args: Positional arguments for func
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        retryable_exceptions: Tuple of exception types to retry on
        **kwargs: Keyword arguments for func

    Returns:
        Result of func

    Raises:
        Last exception if all retries exhausted
    """
    last_exception: Optional[Exception] = None

    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except retryable_exceptions as e:
            last_exception = e

            if attempt < max_retries:
                # Calculate delay with exponential backoff
                delay = min(base_delay * (2 ** attempt), max_delay)

                logger.warning(
                    "retry_after_error",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    delay_seconds=delay,
                    error_type=type(e).__name__,
                    error_message=str(e)[:200]
                )

                await asyncio.sleep(delay)
            else:
                logger.error(
                    "all_retries_exhausted",
                    attempts=max_retries + 1,
                    error_type=type(e).__name__,
                    error_message=str(e)[:200]
                )
        except Exception as e:
            # Non-retryable exception, raise immediately
            logger.error(
                "non_retryable_error",
                error_type=type(e).__name__,
                error_message=str(e)[:200]
            )
            raise

    # All retries exhausted
    if last_exception:
        raise last_exception


def retry_on_error(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    retryable_exceptions: Tuple[Type[Exception], ...] = RETRYABLE_ERRORS
):
    """
    Decorator for async functions to add retry with exponential backoff.

    Usage:
        @retry_on_error(max_retries=3)
        async def my_api_call():
            ...

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await async_retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                retryable_exceptions=retryable_exceptions,
                **kwargs
            )
        return wrapper
    return decorator


# Pre-configured retry decorators for common use cases
retry_ai_call = retry_on_error(
    max_retries=3,
    base_delay=1.0,
    max_delay=10.0,
    retryable_exceptions=(
        TimeoutError,
        ConnectionError,
        asyncio.TimeoutError,
    )
)


def is_rate_limit_error(error: Exception) -> bool:
    """
    Check if an error is a rate limit error from AI providers.

    Args:
        error: Exception to check

    Returns:
        True if this is a rate limit error
    """
    error_str = str(error).lower()
    return any(indicator in error_str for indicator in [
        "rate limit",
        "ratelimit",
        "429",
        "too many requests",
        "quota exceeded"
    ])
