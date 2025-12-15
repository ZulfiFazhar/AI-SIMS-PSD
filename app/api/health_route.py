from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

from app.services.health import health as health_service

router = APIRouter()


# Response Schema
class HealthCheckResponse(BaseModel):
    """Schema for health check response"""

    status: str = Field(..., description="Response status", example="success")
    message: str = Field(
        ..., description="Response message", example="All systems operational"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Health check data",
        example={
            "service": "ai-inkubator",
            "status": "healthy",
            "timestamp": "2025-12-15 10:30:00",
            "environment": "development",
            "version": "0.1.0",
            "checks": {
                "database": {
                    "status": "healthy",
                    "connected": True,
                    "version": "8.0.40",
                },
                "firebase": {
                    "status": "healthy",
                    "initialized": True,
                    "project_id": "your-project-id",
                },
            },
        },
    )


# Response Examples
HEALTH_RESPONSES = {
    200: {
        "description": "All systems operational",
        "content": {
            "application/json": {
                "example": {
                    "status": "success",
                    "message": "All systems operational",
                    "data": {
                        "service": "ai-inkubator",
                        "status": "healthy",
                        "timestamp": "2025-12-15 10:30:00",
                        "environment": "development",
                        "version": "0.1.0",
                        "checks": {
                            "database": {
                                "status": "healthy",
                                "connected": True,
                                "version": "8.0.40",
                            },
                            "firebase": {
                                "status": "healthy",
                                "initialized": True,
                                "project_id": "your-project-id",
                            },
                        },
                    },
                }
            }
        },
    },
    500: {
        "description": "Some systems are unhealthy or degraded",
        "content": {
            "application/json": {
                "example": {
                    "status": "error",
                    "message": "Some systems are unhealthy",
                    "data": {
                        "service": "ai-inkubator",
                        "status": "degraded",
                        "timestamp": "2025-12-15 10:30:00",
                        "environment": "development",
                        "version": "0.1.0",
                        "checks": {
                            "database": {
                                "status": "unhealthy",
                                "connected": False,
                                "error": "Connection refused",
                            },
                            "firebase": {
                                "status": "healthy",
                                "initialized": True,
                                "project_id": "your-project-id",
                            },
                        },
                    },
                }
            }
        },
    },
}


@router.get(
    "/health",
    tags=["health"],
    response_model=HealthCheckResponse,
    summary="Service Health Check",
    description="Returns the health status of the service including database and Firebase connectivity",
    responses=HEALTH_RESPONSES,
)
async def health():
    """
    Comprehensive health check endpoint.

    Performs checks on:
    - **Database**: MySQL connectivity and version
    - **Firebase**: Admin SDK initialization status
    - **Service**: Overall service status and environment info

    Returns `200 OK` if all systems are healthy, or error status with details if any system is degraded.
    """
    return health_service()
