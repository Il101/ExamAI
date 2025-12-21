from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


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

    # Notification Settings
    notification_exam_ready: bool
    notification_study_reminders: bool
    notification_product_updates: bool
    study_days: list[int] = Field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6])

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Update user profile request"""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    preferred_language: Optional[str] = None
    timezone: Optional[str] = None
    daily_study_goal_minutes: Optional[int] = Field(None, ge=0, le=480)
    notification_exam_ready: Optional[bool] = None
    notification_study_reminders: Optional[bool] = None
    notification_product_updates: Optional[bool] = None
    study_days: Optional[list[int]] = None


class ChangePasswordRequest(BaseModel):
    """Change password request"""

    current_password: str
    new_password: str = Field(..., min_length=8)
