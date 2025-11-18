from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe"
            }
        }


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Email verification request"""
    token: str
