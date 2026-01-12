import firebase_admin
from firebase_admin import credentials, auth
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> None:
    """
    Initialize Firebase Admin SDK.
    Call this function on application startup.
    """
    global _firebase_app

    if _firebase_app is not None:
        logger.warning("Firebase already initialized")
        return

    try:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _firebase_app = firebase_admin.initialize_app(
            cred,
            {
                "projectId": settings.firebase_project_id,
            },
        )
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        raise


def close_firebase() -> None:
    """
    Close Firebase connection.
    Call this function on application shutdown.
    """
    global _firebase_app

    if _firebase_app:
        try:
            firebase_admin.delete_app(_firebase_app)
            _firebase_app = None
            logger.info("Firebase connection closed")
        except Exception as e:
            logger.error(f"Error closing Firebase: {e}")


def verify_firebase_token(token: str) -> dict:
    """
    Verify Firebase ID token and return decoded token.

    Args:
        token: Firebase ID token from client

    Returns:
        Decoded token containing user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except auth.ExpiredIdTokenError:
        logger.warning("Firebase token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.RevokedIdTokenError:
        logger.warning("Firebase token revoked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except auth.InvalidIdTokenError:
        logger.warning("Invalid Firebase token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Error verifying Firebase token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


security = HTTPBearer()


async def get_firebase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency to extract Firebase token from Authorization header.
    Does not verify the token - use this for login/register endpoints.

    Usage:
        @router.post("/login")
        async def login(token: str = Depends(get_firebase_token)):
            # Token will be extracted from Authorization: Bearer <token>
            ...
    """
    return credentials.credentials


async def get_current_user_firebase_uid(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    FastAPI dependency to get current user's Firebase UID from token.

    Usage:
        @router.get("/protected")
        async def protected_route(firebase_uid: str = Depends(get_current_user_firebase_uid)):
            # Use firebase_uid to fetch user from database
            ...
    """
    token = credentials.credentials
    decoded_token = verify_firebase_token(token)
    firebase_uid = decoded_token.get("uid")

    if not firebase_uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )

    return firebase_uid


async def get_firebase_user_info(firebase_uid: str) -> dict:
    """
    Get user information from Firebase Auth.

    Args:
        firebase_uid: Firebase user ID

    Returns:
        Dictionary containing user information
    """
    try:
        user = auth.get_user(firebase_uid)
        return {
            "firebase_uid": user.uid,
            "email": user.email,
            "display_name": user.display_name,
            "photo_url": user.photo_url,
            "phone_number": user.phone_number,
            "email_verified": user.email_verified,
        }
    except auth.UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found in Firebase",
        )
    except Exception as e:
        logger.error(f"Error fetching Firebase user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error fetching user information",
        )
