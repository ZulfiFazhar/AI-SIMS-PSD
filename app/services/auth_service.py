import logging

from fastapi import HTTPException

from app.models.dto.auth_dto import UserUpdateRequest, UserResponse, AuthResponse
from app.core.middleware import verify_firebase_token, get_firebase_user_info
from app.core.schema import BaseResponse, create_success_response, create_error_response
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Service class for authentication and user management"""

    def __init__(self, user_repository: UserRepository):
        self.user_repo = user_repository

    async def login_or_register(self, firebase_token: str) -> BaseResponse:
        """
        Authenticate user with Firebase token.
        If user doesn't exist in database, create new user.
        If user exists, update last_login.

        Args:
            firebase_token: Firebase ID token from client

        Returns:
            BaseResponse with AuthResponse data
        """
        try:
            decoded_token = verify_firebase_token(firebase_token)
            firebase_uid = decoded_token.get("uid")

            if not firebase_uid:
                return create_error_response(message="Invalid token: missing user ID")

            firebase_user = await get_firebase_user_info(firebase_uid)

            user = self.user_repo.get_by_firebase_uid(firebase_uid)

            is_new_user = False

            if not user:
                try:
                    user = self.user_repo.create(
                        firebase_uid=firebase_user["firebase_uid"],
                        email=firebase_user["email"],
                        display_name=firebase_user["display_name"],
                        photo_url=firebase_user["photo_url"],
                        phone_number=firebase_user["phone_number"],
                        email_verified=firebase_user["email_verified"],
                    )
                    is_new_user = True
                    logger.info(f"New user created: {user.email}")
                except Exception as e:
                    logger.error(f"Failed to create user: {e}")
                    self.user_repo.rollback()
                    return create_error_response(
                        message="Failed to create user account. Please try again."
                    )
            else:
                self.user_repo.update_last_login(user)
                self.user_repo.update(
                    user,
                    email=firebase_user["email"],
                    display_name=firebase_user.get("display_name") or user.display_name,
                    photo_url=firebase_user.get("photo_url") or user.photo_url,
                    email_verified=firebase_user["email_verified"],
                )
                logger.info(f"User logged in: {user.email}")

            self.user_repo.commit()
            self.user_repo.refresh(user)

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
            self.user_repo.rollback()
            return create_error_response(
                message="Authentication failed. Please try again."
            )

    def get_user_profile(self, firebase_uid: str) -> BaseResponse:
        """
        Get user profile by Firebase UID.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            BaseResponse with UserResponse data
        """
        try:
            user = self.user_repo.get_by_firebase_uid(firebase_uid)

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

    def update_user_profile(
        self, firebase_uid: str, update_data: UserUpdateRequest
    ) -> BaseResponse:
        """
        Update user profile.

        Args:
            firebase_uid: Firebase user ID
            update_data: User update request data

        Returns:
            BaseResponse with updated UserResponse data
        """
        try:
            user = self.user_repo.get_by_firebase_uid(firebase_uid)

            if not user:
                return create_error_response(message="User not found")

            self.user_repo.update(
                user,
                display_name=update_data.display_name,
                phone_number=update_data.phone_number,
            )

            self.user_repo.commit()
            self.user_repo.refresh(user)

            user_response = UserResponse.model_validate(user)

            return create_success_response(
                message="Profile updated successfully", data=user_response.model_dump()
            )

        except Exception as e:
            logger.error(f"Error updating user profile: {e}")
            self.user_repo.rollback()
            return create_error_response(message="Failed to update profile")

    def deactivate_user(self, firebase_uid: str) -> BaseResponse:
        """
        Deactivate user account.

        Args:
            firebase_uid: Firebase user ID

        Returns:
            BaseResponse with success/error message
        """
        try:
            user = self.user_repo.get_by_firebase_uid(firebase_uid)

            if not user:
                return create_error_response(message="User not found")

            self.user_repo.deactivate(user)
            self.user_repo.commit()

            return create_success_response(message="Account deactivated successfully")

        except Exception as e:
            logger.error(f"Error deactivating user: {e}")
            self.user_repo.rollback()
            return create_error_response(message="Failed to deactivate account")
