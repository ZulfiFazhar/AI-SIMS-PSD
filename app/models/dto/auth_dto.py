from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ============= Request DTOs =============


class UserLoginRequest(BaseModel):
    """Request body for user login with Firebase token"""

    firebase_token: str

    class Config:
        json_schema_extra = {
            "example": {"firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE..."}
        }


class UserUpdateRequest(BaseModel):
    """Request body for updating user profile"""

    display_name: Optional[str] = None
    phone_number: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {"display_name": "John Doe", "phone_number": "+6281234567890"}
        }


# ============= Response DTOs =============


class UserResponse(BaseModel):
    """User information response"""

    id: str
    firebase_uid: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool
    email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "firebase_uid": "abc123xyz789",
                "email": "user@example.com",
                "display_name": "John Doe",
                "photo_url": "https://example.com/photo.jpg",
                "phone_number": "+6281234567890",
                "is_active": True,
                "email_verified": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00",
                "last_login": "2024-01-01T12:00:00",
            }
        }


class AuthResponse(BaseModel):
    """Authentication response with user info and token"""

    user: UserResponse
    is_new_user: bool

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": 1,
                    "firebase_uid": "abc123xyz789",
                    "email": "user@example.com",
                    "display_name": "John Doe",
                    "is_active": True,
                    "email_verified": True,
                },
                "is_new_user": False,
            }
        }
