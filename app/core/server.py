from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

import time
import logging

from app.api import health_route
from app.api.router import router_v1
from app.core.config import settings
from app.core.schema import create_success_response
from app.core.database import init_db, close_db
from app.core.middleware import init_firebase, close_firebase

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    logger.info("Starting application...")
    try:
        init_firebase()
        init_db()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        close_firebase()
        close_db()
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()), format=settings.log_format
    )


def setup_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.is_production:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    @app.middleware("http")
    async def add_timing(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} ({process_time:.4f}s)"
        )
        return response

    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
            }
        )
        return response


def index_route(app) -> FastAPI:
    """Define the index route for the FastAPI application"""

    @app.get("/", tags=["welcome"])
    def _():
        return create_success_response(
            data={"message": "Welcome to FastAPI UV Backend!"}
        )

    return app


def v1_route(app) -> FastAPI:
    """Include API routes"""
    app.include_router(router_v1, prefix="/api")
    return app


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""
    setup_logging()

    app = FastAPI(
        title=settings.app_name,
        description="FastAPI UV Backend with Firebase Auth and MySQL",
        version=settings.version,
        lifespan=lifespan,
    )

    setup_middlewares(app)
    index_route(app)

    app.include_router(health_route.router)

    v1_route(app)

    logger.info("FastAPI application configured successfully")

    return app
