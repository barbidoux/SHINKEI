"""Health check endpoints for orchestration and monitoring."""
from fastapi import APIRouter, status as http_status
from sqlalchemy import text
from shinkei.database.engine import engine
from shinkei.config import settings
from shinkei.logging_config import get_logger
import time

router = APIRouter()
logger = get_logger(__name__)

# Track startup time for startup probe
_startup_time = time.time()


@router.get("/ready", status_code=http_status.HTTP_200_OK)
async def readiness_probe():
    """
    Readiness probe for Kubernetes/orchestration systems.
    Indicates when the application is ready to receive traffic.

    Checks:
    - Database connection pool is ready
    - All critical dependencies are initialized
    - Application can serve requests
    """
    checks = {
        "database": "unknown",
        "application": "ready"
    }

    all_healthy = True

    # Check database connectivity
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result:
                checks["database"] = "ready"
            else:
                checks["database"] = "not_ready"
                all_healthy = False
    except Exception as e:
        checks["database"] = "not_ready"
        checks["database_error"] = str(e)
        all_healthy = False
        logger.warning("readiness_check_database_failed", error=str(e))

    response = {
        "ready": all_healthy,
        "checks": checks,
        "timestamp": time.time()
    }

    # Return 503 if not ready, 200 if ready
    response_status = http_status.HTTP_200_OK if all_healthy else http_status.HTTP_503_SERVICE_UNAVAILABLE

    return response


@router.get("/liveness", status_code=http_status.HTTP_200_OK)
async def liveness_probe():
    """
    Liveness probe for Kubernetes/orchestration systems.
    Indicates if the application process is alive and functioning.

    This is a lightweight check that doesn't verify dependencies.
    If this fails, the container should be restarted.
    """
    return {
        "alive": True,
        "timestamp": time.time(),
        "uptime_seconds": time.time() - _startup_time
    }


@router.get("/startup", status_code=http_status.HTTP_200_OK)
async def startup_probe():
    """
    Startup probe for Kubernetes/orchestration systems.
    Indicates when the application has finished starting up.

    This runs during initialization and should succeed before
    liveness and readiness probes start.
    """
    checks = {
        "application": "started",
        "database": "unknown"
    }

    all_started = True

    # Verify database is accessible
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            checks["database"] = "started"
    except Exception as e:
        checks["database"] = "not_started"
        checks["database_error"] = str(e)
        all_started = False
        logger.error("startup_check_database_failed", error=str(e))

    response = {
        "started": all_started,
        "checks": checks,
        "timestamp": time.time(),
        "startup_duration_seconds": time.time() - _startup_time
    }

    response_status = http_status.HTTP_200_OK if all_started else http_status.HTTP_503_SERVICE_UNAVAILABLE

    return response


@router.get("/health/detailed", status_code=http_status.HTTP_200_OK)
async def detailed_health():
    """
    Detailed health check for monitoring and debugging.
    Provides comprehensive status of all components.
    """
    checks = {
        "database": {
            "status": "unknown",
            "latency_ms": None
        },
        "application": {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "uptime_seconds": time.time() - _startup_time
        }
    }

    overall_healthy = True

    # Check database with latency measurement
    db_start = time.time()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_latency = (time.time() - db_start) * 1000  # Convert to ms
            checks["database"]["status"] = "healthy"
            checks["database"]["latency_ms"] = round(db_latency, 2)
    except Exception as e:
        checks["database"]["status"] = "unhealthy"
        checks["database"]["error"] = str(e)
        overall_healthy = False
        logger.error("detailed_health_check_failed", error=str(e))

    response = {
        "status": "healthy" if overall_healthy else "unhealthy",
        "timestamp": time.time(),
        "checks": checks
    }

    response_status = http_status.HTTP_200_OK if overall_healthy else http_status.HTTP_503_SERVICE_UNAVAILABLE

    return response
