from app.core.server import create_application
from app.core.config import settings
from app.core.schema import create_success_response, BaseResponse
from app.core.health import router as health_router
from app.api.routes import router as api_router
import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()

# Create configured application
app = create_application()

# Root endpoint
@app.get("/", tags=["welcome"], response_model=BaseResponse)
def welcome():
    """Welcome endpoint with basic service information"""
    return create_success_response(
        message=f"Welcome to {settings.app_name}!",
        data={
            "service": settings.app_name,
            "version": "1.0.0",
            "environment": settings.environment,
            "status": "running",
            "docs_url": "/docs" if not settings.is_production else "disabled"
        }
    )

# Include routers
app.include_router(health_router)
app.include_router(api_router)

# Export app for uvicorn
__all__ = ["app"]