import logging
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.user_model import User, UserRole
from app.core.utils import generate_short_id

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for User database operations"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_firebase_uid(self, firebase_uid: str) -> Optional[User]:
        """
        Get user by Firebase UID.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.firebase_uid == firebase_uid).first()

    def get_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()

    def create(
        self,
        firebase_uid: str,
        email: str,
        display_name: Optional[str] = None,
        photo_url: Optional[str] = None,
        phone_number: Optional[str] = None,
        email_verified: bool = False,
        role: UserRole = UserRole.GUEST,
    ) -> User:
        """
        Create a new user with unique ID generation.

        Args:
            firebase_uid: Firebase user ID
            email: User email
            display_name: User display name
            photo_url: User photo URL
            phone_number: User phone number
            email_verified: Email verification status
            role: User role (default: GUEST)

        Returns:
            Created User object

        Raises:
            Exception: If unable to generate unique ID after max retries
        """
        # Generate unique ID with collision check
        max_retries = 10
        user_id = None

        for attempt in range(max_retries):
            user_id = generate_short_id()
            existing = self.db.query(User).filter(User.id == user_id).first()
            if not existing:
                break
            if attempt == max_retries - 1:
                logger.error("Failed to generate unique user ID after max retries")
                raise Exception("Failed to generate unique user ID")

        user = User(
            id=user_id,
            firebase_uid=firebase_uid,
            email=email,
            display_name=display_name,
            photo_url=photo_url,
            phone_number=phone_number,
            email_verified=email_verified,
            role=role,
            last_login=datetime.now(timezone.utc),
        )

        self.db.add(user)
        return user

    def update(
        self,
        user: User,
        display_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        photo_url: Optional[str] = None,
        email: Optional[str] = None,
        email_verified: Optional[bool] = None,
        role: Optional[UserRole] = None,
    ) -> User:
        """
        Update user information.

        Args:
            user: User object to update
            display_name: New display name
            phone_number: New phone number
            photo_url: New photo URL
            email: New email
            email_verified: New email verification status
            role: New role

        Returns:
            Updated User object
        """
        if display_name is not None:
            user.display_name = display_name

        if phone_number is not None:
            user.phone_number = phone_number

        if photo_url is not None:
            user.photo_url = photo_url

        if email is not None:
            user.email = email

        if email_verified is not None:
            user.email_verified = email_verified

        if role is not None:
            user.role = role

        user.updated_at = datetime.now(timezone.utc)
        return user

    def update_last_login(self, user: User) -> User:
        """
        Update user's last login timestamp.

        Args:
            user: User object to update

        Returns:
            Updated User object
        """
        user.last_login = datetime.now(timezone.utc)
        return user

    def deactivate(self, user: User) -> User:
        """
        Deactivate user account.

        Args:
            user: User object to deactivate

        Returns:
            Updated User object
        """
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        return user

    def activate(self, user: User) -> User:
        """
        Activate user account.

        Args:
            user: User object to activate

        Returns:
            Updated User object
        """
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        return user

    def update_role(self, user: User, role: UserRole) -> User:
        """
        Update user role.

        Args:
            user: User object to update
            role: New role to assign

        Returns:
            Updated User object
        """
        user.role = role
        user.updated_at = datetime.now(timezone.utc)
        logger.info(f"User {user.id} role updated to {role.value}")
        return user

    def commit(self):
        """Commit database transaction"""
        self.db.commit()

    def rollback(self):
        """Rollback database transaction"""
        self.db.rollback()

    def refresh(self, user: User):
        """
        Refresh user object from database.

        Args:
            user: User object to refresh
        """
        self.db.refresh(user)
