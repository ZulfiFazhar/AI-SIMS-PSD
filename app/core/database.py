from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=settings.is_development,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    
    WARNING: This function uses Base.metadata.create_all() which is only 
    suitable for development. For production, use Alembic migrations instead.
    
    Behavior:
    - Development: Creates all tables automatically (convenient for local dev)
    - Production: Should use Alembic migrations for proper version control
    
    Important: Models must be imported before calling this function
    so that SQLAlchemy can discover them via Base.metadata
    """

    # import app.models  # noqa: F401
    
    # if settings.is_production:
    #     logger.warning(
    #         "init_db() called in production mode. "
    #         "Consider using Alembic migrations instead of Base.metadata.create_all()"
    #     )
        # In production, we skip auto-creation and rely on migrations
        # Uncomment the line below if you want to disable auto-creation in production
        # logger.info("Skipping auto table creation in production - use 'uv run alembic upgrade head'")
        # return
    
    try:
        # Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully (development mode)")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def close_db() -> None:
    """
    Close database connections.
    Call this function on application shutdown.
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
