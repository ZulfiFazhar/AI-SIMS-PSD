from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_user_firebase_uid, get_firebase_token
from app.core.schema import BaseResponse
from app.models.dto.auth_dto import UserUpdateRequest
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService with UserRepository"""
    user_repository = UserRepository(db)
    return AuthService(user_repository)


@router.post("/login", response_model=BaseResponse)
async def login(
    token: str = Depends(get_firebase_token),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Authenticate user with Firebase token.

    This endpoint:
    - Verifies Firebase ID token
    - Creates new user if not exists
    - Updates last_login if user exists
    - Returns user information

    **Client should:**
    1. Authenticate with Firebase (Google, Email/Password, etc.)
    2. Get ID token from Firebase: `user.getIdToken()`
    3. Send token in Authorization header: `Authorization: Bearer <token>`

    **Example:**
    ```
    POST /api/auth/login
    Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI...
    ```
    """
    return await auth_service.login_or_register(token)


@router.get("/me", response_model=BaseResponse)
async def get_current_user(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Get current authenticated user's profile.

    Requires authentication header:
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    return auth_service.get_user_profile(firebase_uid)


@router.put("/me", response_model=BaseResponse)
async def update_profile(
    request: UserUpdateRequest,
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Update current user's profile.

    Requires authentication header:
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    return auth_service.update_user_profile(firebase_uid, request)


@router.delete("/me", response_model=BaseResponse)
async def deactivate_account(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Deactivate current user's account.

    Requires authentication header:
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    return auth_service.deactivate_user(firebase_uid)
