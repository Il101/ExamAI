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
    start_time: datetime
    end_time: Optional[datetime]
    duration_minutes: int
    status: str

    class Config:
        from_attributes = True
