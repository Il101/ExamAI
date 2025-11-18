from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserResponse(BaseModel):
    """User profile response"""
    id: UUID
    email: str
    full_name: str
    role: str
    subscription_plan: str
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    # Preferences
    preferred_language: str
    timezone: str
    daily_study_goal_minutes: int
    
    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Update user profile request"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    daily_study_goal_minutes: Optional[int] = Field(None, ge=0, le=480)


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str = Field(..., min_length=8)
