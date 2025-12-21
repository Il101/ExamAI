from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

class CourseBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    subject: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    semester_start: Optional[date] = None
    semester_end: Optional[date] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    subject: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    semester_start: Optional[date] = None
    semester_end: Optional[date] = None
    is_archived: Optional[bool] = None

class CourseStats(BaseModel):
    exam_count: int = 0
    topic_count: int = 0
    completed_topics: int = 0
    due_flashcards_count: int = 0
    total_actual_study_minutes: int = 0
    total_planned_study_minutes: int = 0
    average_difficulty: float = 0.0
    progress_percentage: float = 0.0

class CourseResponse(CourseBase):
    id: UUID
    user_id: UUID
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    # Optional stats
    stats: Optional[CourseStats] = None

    class Config:
        from_attributes = True

class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
