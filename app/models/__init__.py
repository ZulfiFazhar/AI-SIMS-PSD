"""
Models package.

This module imports all SQLAlchemy ORM models to ensure they are
registered with Base.metadata before database initialization.

Import this module in init_db() to automatically register all models.
"""

from app.models.user_model import User
from app.models.tenant_model import Tenant, BusinessDocument

# Export models for easy import elsewhere
__all__ = ["User"]
