"""Rate limiting middleware using slowapi."""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from shinkei.config import settings
from shinkei.logging_config import get_logger

logger = get_logger(__name__)

# Create limiter instance
# Uses client IP address for rate limiting
# In production, consider using Redis for distributed rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri="memory://",  # In-memory storage (use redis:// for production with multiple workers)
    strategy="fixed-window",  # Simple fixed window strategy
    headers_enabled=True,  # Add rate limit headers to response
)


def setup_rate_limiter(app):
    """
    Configure rate limiting for the FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Add limiter state to app
    app.state.limiter = limiter

    # Add exception handler for rate limit exceeded
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    logger.info(
        "rate_limiter_configured",
        default_limit_per_minute=settings.rate_limit_per_minute,
        storage="memory"
    )


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Logs the rate limit event and returns a 429 response.
    """
    logger.warning(
        "rate_limit_exceeded",
        path=request.url.path,
        method=request.method,
        client=get_remote_address(request),
        limit=exc.detail
    )

    return _rate_limit_exceeded_handler(request, exc)


# Rate limit decorators for different endpoint types
# Usage: @limiter.limit("5/minute") above your endpoint function

# Strict limits for authentication endpoints
AUTH_RATE_LIMIT = "5/minute"

# Moderate limits for write operations
WRITE_RATE_LIMIT = "30/minute"

# Generous limits for read operations
READ_RATE_LIMIT = "100/minute"

# Very strict limits for expensive operations (AI generation)
GENERATION_RATE_LIMIT = "10/minute"

# No limit for health checks
HEALTH_CHECK_EXEMPT = "1000/minute"
