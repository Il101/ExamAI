"""
Health check endpoints for monitoring and load balancers.

Provides basic and detailed health checks for the application and its dependencies.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
import logging

from app.db.session import get_db
from app.core.config import settings

router = APIRouter(tags=["Health"])
logger = logging.getLogger(__name__)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint.

    Returns a simple status for load balancers and Docker health checks.
    Does not check dependencies to avoid false positives.

    Returns:
        Dict with status and service name
    """
    return {
        "status": "healthy",
        "service": "examai-backend",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/health/detailed", status_code=status.HTTP_200_OK)
async def detailed_health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed health check with dependency checks.

    Checks the health of:
    - Database connection
    - Redis connection
    - Celery workers

    Returns:
        Dict with overall status and individual component statuses

    Raises:
        HTTPException: If critical components are unhealthy
    """
    health = {
        "status": "healthy",
        "service": "examai-backend",
        "environment": settings.ENVIRONMENT,
        "checks": {},
    }

    # Check database
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful",
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health["checks"]["database"] = {"status": "unhealthy", "message": str(e)}
        health["status"] = "unhealthy"

    # Check Redis/Celery
    try:
        from app.tasks.celery_app import celery_app

        # Check if Redis is responding
        redis_client = celery_app.backend.client
        redis_client.ping()
        health["checks"]["redis"] = {
            "status": "healthy",
            "message": "Redis connection successful",
        }

        # Check Celery workers
        try:
            stats = celery_app.control.inspect().stats()
            if stats:
                worker_count = len(stats)
                health["checks"]["celery_workers"] = {
                    "status": "healthy",
                    "message": f"{worker_count} worker(s) available",
                    "workers": worker_count,
                }
            else:
                health["checks"]["celery_workers"] = {
                    "status": "degraded",
                    "message": "No workers available",
                }
                health["status"] = "degraded"
        except Exception as e:
            logger.warning(f"Celery worker check failed: {e}")
            health["checks"]["celery_workers"] = {
                "status": "degraded",
                "message": f"Cannot inspect workers: {str(e)}",
            }
            if health["status"] == "healthy":
                health["status"] = "degraded"

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health["checks"]["redis"] = {"status": "unhealthy", "message": str(e)}
        health["status"] = "unhealthy"

    # Return 503 if unhealthy
    if health["status"] == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=health
        )

    return health


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Readiness check for Kubernetes/orchestration systems.

    Indicates whether the service is ready to accept traffic.
    Checks critical dependencies only.

    Returns:
        Dict with ready status

    Raises:
        HTTPException: If service is not ready
    """
    try:
        # Check database
        await db.execute(text("SELECT 1"))

        return {"status": "ready", "service": "examai-backend"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "not_ready", "message": str(e)},
        )


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Kubernetes/orchestration systems.

    Indicates whether the service is alive and should not be restarted.
    Does not check external dependencies.

    Returns:
        Dict with alive status
    """
    return {"status": "alive", "service": "examai-backend"}
