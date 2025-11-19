from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


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
