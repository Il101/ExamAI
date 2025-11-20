from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class AdminUserResponse(BaseModel):
    """User details for admin view"""

    id: UUID
    email: str
    full_name: str
    role: str
    subscription_plan: str
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Paginated user list"""

    users: List[AdminUserResponse]
    total: int
    skip: int
    limit: int


class AdminUserUpdate(BaseModel):
    """Update user fields (admin only)"""

    role: Optional[str] = None
    subscription_plan: Optional[str] = None
    is_verified: Optional[bool] = None


class SystemStatistics(BaseModel):
    """System-wide statistics"""

    total_users: int
    total_exams: int
    total_topics: int
    total_reviews: int
    active_users_last_7_days: int
    active_users_last_30_days: int
    users_by_plan: dict
    users_by_role: dict


class AdminExamResponse(BaseModel):
    """Exam details for admin view"""

    id: UUID
    user_id: UUID
    user_email: str
    title: str
    subject: str
    status: str
    created_at: datetime
    topic_count: int

    class Config:
        from_attributes = True


class ExamListResponse(BaseModel):
    """Paginated exam list"""

    exams: List[AdminExamResponse]
    total: int
    skip: int
    limit: int
