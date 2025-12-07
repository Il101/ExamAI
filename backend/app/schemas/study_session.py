from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class StudySessionCreate(BaseModel):
    exam_id: UUID
    duration_minutes: int


class StudySessionResponse(BaseModel):
    id: UUID
    user_id: UUID
    exam_id: UUID
    started_at: datetime
    ended_at: Optional[datetime]
    pomodoro_duration_minutes: int
    pomodoros_completed: int
    is_active: bool

    class Config:
        from_attributes = True
