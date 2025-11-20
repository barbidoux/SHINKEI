"""Shinkei Backend Entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from shinkei.config import settings
from shinkei.logging_config import configure_logging, get_logger
from shinkei.database.engine import init_db, close_db, engine
from shinkei.middleware.security_headers import SecurityHeadersMiddleware
from shinkei.middleware.rate_limiter import setup_rate_limiter
from shinkei.exceptions import ShinkeiException

from shinkei.api.v1.api import api_router

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("application_starting", environment=settings.environment)
    if settings.environment == "development":
        await init_db()
        logger.info("database_tables_created")

    yield

    # Shutdown
    await close_db()
    logger.info("application_shutdown_complete")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    docs_url=f"{settings.api_v1_prefix}/docs",
    redoc_url=f"{settings.api_v1_prefix}/redoc",
    lifespan=lifespan,
)

# Configure CORS middleware with security-hardened settings
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.cors_origins],
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicit methods only
        allow_headers=[
            "Authorization",
            "Content-Type",
            "Accept",
            "Origin",
            "User-Agent",
            "X-Requested-With",
        ],  # Explicit headers only, no wildcards
        max_age=settings.cors_max_age,  # Cache preflight responses
    )
    logger.info(
        "cors_configured",
        origins_count=len(settings.cors_origins),
        allow_credentials=settings.cors_allow_credentials
    )

# Add security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Setup rate limiting
setup_rate_limiter(app)

# Global exception handler for custom Shinkei exceptions
@app.exception_handler(ShinkeiException)
async def shinkei_exception_handler(request: Request, exc: ShinkeiException):
    """
    Handle all custom Shinkei exceptions globally.

    Logs the error and returns a standardized JSON response.
    """
    logger.warning(
        "shinkei_exception",
        exception_type=exc.__class__.__name__,
        message=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "type": exc.__class__.__name__,
                "status_code": exc.status_code,
                "details": exc.details if settings.environment != "production" else {}
            }
        }
    )

app.include_router(api_router, prefix=settings.api_v1_prefix)

@app.get("/health")
async def health_check():
    """
    Health check endpoint with database verification.
    Returns overall health status including database connectivity.
    """
    health_status = {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "checks": {
            "database": "unknown"
        }
    }

    # Check database connectivity
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = "unhealthy"
        health_status["error"] = str(e)
        logger.error("health_check_failed", error=str(e))

    # Return appropriate status code
    response_status = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return health_status
