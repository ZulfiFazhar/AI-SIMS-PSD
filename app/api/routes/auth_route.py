from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_firebase_uid
from app.core.schema import BaseResponse
from app.models.dto.auth_dto import UserLoginRequest, UserUpdateRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=BaseResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
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
    3. Send token to this endpoint
    """
    return await AuthService.login_or_register(request.firebase_token, db)


@router.get("/me", response_model=BaseResponse)
async def get_current_user(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db),
):
    """
    Get current authenticated user's profile.

    Requires authentication header:
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    return AuthService.get_user_profile(firebase_uid, db)


@router.put("/me", response_model=BaseResponse)
async def update_profile(
    request: UserUpdateRequest,
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db),
):
    """
    Update current user's profile.

    Requires authentication header:
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    return AuthService.update_user_profile(firebase_uid, request, db)


@router.delete("/me", response_model=BaseResponse)
async def deactivate_account(
    firebase_uid: str = Depends(get_current_user_firebase_uid),
    db: Session = Depends(get_db),
):
    """
    Deactivate current user's account.

    Requires authentication header:
    ```
    Authorization: Bearer <firebase_id_token>
    ```
    """
    return AuthService.deactivate_user(firebase_uid, db)
