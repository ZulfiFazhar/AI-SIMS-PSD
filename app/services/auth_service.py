from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi import HTTPException
import logging

from app.models.user_model import User, generate_short_id
from app.models.dto.auth_dto import UserUpdateRequest, UserResponse, AuthResponse
from app.core.security import verify_firebase_token, get_firebase_user_info
from app.core.schema import BaseResponse, create_success_response, create_error_response

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication and user management"""

    @staticmethod
    async def login_or_register(firebase_token: str, db: Session) -> BaseResponse:
        """
        Authenticate user with Firebase token.
        If user doesn't exist in database, create new user.
        If user exists, update last_login.

        Args:
            firebase_token: Firebase ID token from client
            db: Database session

        Returns:
            BaseResponse with AuthResponse data
        """
        try:
            decoded_token = verify_firebase_token(firebase_token)
            firebase_uid = decoded_token.get("uid")

            if not firebase_uid:
                return create_error_response(message="Invalid token: missing user ID")

            firebase_user = await get_firebase_user_info(firebase_uid)

            user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

            is_new_user = False

            if not user:
                # Generate unique ID with collision check
                max_retries = 10
                for attempt in range(max_retries):
                    new_user_id = generate_short_id()
                    existing = db.query(User).filter(User.id == new_user_id).first()
                    if not existing:
                        break
                    if attempt == max_retries - 1:
                        logger.error("Failed to generate unique user ID after max retries")
                        return create_error_response(
                            message="Failed to create user account. Please try again."
                        )
                
                user = User(
                    id=new_user_id,
                    firebase_uid=firebase_user["firebase_uid"],
                    email=firebase_user["email"],
                    display_name=firebase_user["display_name"],
                    photo_url=firebase_user["photo_url"],
                    phone_number=firebase_user["phone_number"],
                    email_verified=firebase_user["email_verified"],
                    last_login=datetime.now(timezone.utc),
                )
                db.add(user)
                is_new_user = True
                logger.info(f"New user created: {user.email}")
            else:
                user.last_login = datetime.now(timezone.utc)

                user.email = firebase_user["email"]
                user.display_name = (
                    firebase_user.get("display_name") or user.display_name
                )
                user.photo_url = firebase_user.get("photo_url") or user.photo_url
                user.email_verified = firebase_user["email_verified"]

                logger.info(f"User logged in: {user.email}")

            db.commit()
            db.refresh(user)

            user_response = UserResponse.model_validate(user)
            auth_response = AuthResponse(user=user_response, is_new_user=is_new_user)

            return create_success_response(
                message="Login successful"
                if not is_new_user
                else "User registered successfully",
                data=auth_response.model_dump(),
            )

        except HTTPException as e:
            return create_error_response(message=e.detail)
        except Exception as e:
            logger.error(f"Error in login_or_register: {e}")
            db.rollback()
            return create_error_response(
                message="Authentication failed. Please try again."
            )

    @staticmethod
    def get_user_profile(firebase_uid: str, db: Session) -> BaseResponse:
        """
        Get user profile by Firebase UID.

        Args:
            firebase_uid: Firebase user ID
            db: Database session

        Returns:
            BaseResponse with UserResponse data
        """
        try:
            user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

            if not user:
                return create_error_response(message="User not found")

            user_response = UserResponse.model_validate(user)

            return create_success_response(
                message="User profile retrieved successfully",
                data=user_response.model_dump(),
            )

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return create_error_response(message="Failed to retrieve user profile")

    @staticmethod
    def update_user_profile(
        firebase_uid: str, update_data: UserUpdateRequest, db: Session
    ) -> BaseResponse:
        """
        Update user profile.

        Args:
            firebase_uid: Firebase user ID
            update_data: User update request data
            db: Database session

        Returns:
            BaseResponse with updated UserResponse data
        """
        try:
            user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

            if not user:
                return create_error_response(message="User not found")

            if update_data.display_name is not None:
                user.display_name = update_data.display_name

            if update_data.phone_number is not None:
                user.phone_number = update_data.phone_number

            user.updated_at = datetime.now(timezone.utc)

            db.commit()
            db.refresh(user)

            user_response = UserResponse.model_validate(user)

            return create_success_response(
                message="Profile updated successfully", data=user_response.model_dump()
            )

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            db.rollback()
            return create_error_response(message="Failed to update profile")

    @staticmethod
    def deactivate_user(firebase_uid: str, db: Session) -> BaseResponse:
        """
        Deactivate user account.

        Args:
            firebase_uid: Firebase user ID
            db: Database session

        Returns:
            BaseResponse with success/error message
        """
        try:
            user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

            if not user:
                return create_error_response(message="User not found")

            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)

            db.commit()

            return create_success_response(message="Account deactivated successfully")

        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            db.rollback()
            return create_error_response(message="Failed to deactivate account")
