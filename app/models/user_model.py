import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Boolean, Enum
from sqlalchemy.dialects.mysql import CHAR

from app.core.database import Base
from app.core.utils import generate_short_id


class UserRole(str, enum.Enum):
    """
    User role enumeration.
    - ADMIN: Full system access, can approve tenant requests
    - TENANT: Approved user with full application access
    - GUEST: Default role after registration, limited access
    """

    ADMIN = "admin"
    TENANT = "tenant"
    GUEST = "guest"


class User(Base):
    """
    User model for storing user information from Firebase Auth.
    This model syncs Firebase users with local MySQL database.
    Uses short 4-character ID for compact identification.
    """

    __tablename__ = "users"

    id = Column(
        CHAR(4),
        primary_key=True,
        default=generate_short_id,
        index=True,
        unique=True,
    )

    # Firebase UID - unique identifier from Firebase Auth
    firebase_uid = Column(String(128), unique=True, nullable=False, index=True)

    # User information
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    phone_number = Column(String(20), nullable=True)

    # User role - default is 'guest' after registration
    role = Column(
        Enum(UserRole),
        default=UserRole.GUEST,
        nullable=False,
        server_default="guest",
    )

    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, firebase_uid={self.firebase_uid})>"

    def to_dict(self):
        """Convert user object to dictionary"""
        return {
            "id": self.id,
            "firebase_uid": self.firebase_uid,
            "email": self.email,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "phone_number": self.phone_number,
            "role": self.role.value if isinstance(self.role, UserRole) else self.role,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
