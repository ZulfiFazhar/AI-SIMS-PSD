import time
import logging
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import firebase_admin

from app.core.schema import create_success_response, create_error_response, BaseResponse
from app.core.database import engine
from app.core.config import settings

logger = logging.getLogger(__name__)


def check_database() -> Dict[str, Any]:
    """
    Check database connectivity and return status.
    """
    try:
        with engine.connect() as connection:
            # Execute a simple query to verify connection
            result = connection.execute(text("SELECT 1"))
            result.fetchone()

            # Get database info
            db_info = connection.execute(text("SELECT VERSION()"))
            version = db_info.fetchone()[0]

            return {
                "status": "healthy",
                "connected": True,
                "version": version.split("-")[0] if version else "unknown",
                "response_time_ms": 0,  # Could add timing here
            }
    except SQLAlchemyError as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }
    except Exception as e:
        logger.error(f"Unexpected error during database check: {e}")
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
        }


def check_firebase() -> Dict[str, Any]:
    """
    Check Firebase Admin SDK initialization status.
    """
    try:
        # Check if Firebase app is initialized
        app = firebase_admin.get_app()

        return {
            "status": "healthy",
            "initialized": True,
            "project_id": app.project_id if app else "unknown",
        }
    except ValueError:
        # Firebase not initialized
        logger.warning("Firebase not initialized")
        return {
            "status": "unhealthy",
            "initialized": False,
            "error": "Firebase Admin SDK not initialized",
        }
    except Exception as e:
        logger.error(f"Firebase health check failed: {e}")
        return {
            "status": "unhealthy",
            "initialized": False,
            "error": str(e),
        }


def health() -> BaseResponse:
    """
    Comprehensive health check for the service.
    Checks:
    - Service uptime and timestamp
    - Database connectivity
    - Firebase Admin SDK status
    - Environment configuration
    """
    try:
        # Perform health checks
        db_health = check_database()
        firebase_health = check_firebase()

        # Determine overall health status
        all_healthy = (
            db_health.get("status") == "healthy"
            and firebase_health.get("status") == "healthy"
        )

        health_data = {
            "service": "ai-inkubator",
            "status": "healthy" if all_healthy else "degraded",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "environment": settings.environment,
            "version": "0.1.0",
            "checks": {
                "database": db_health,
                "firebase": firebase_health,
            },
        }

        if all_healthy:
            return create_success_response(
                message="All systems operational",
                data=health_data,
            )
        else:
            return create_error_response(
                message="Some systems are unhealthy",
                data=health_data,
            )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return create_error_response(
            message="Health check failed",
            data={
                "service": "ai-inkubator",
                "status": "unhealthy",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e),
            },
        )
