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
    exam_date: Optional[datetime] = None

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    subject: Optional[str] = Field(None, min_length=2, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    semester_start: Optional[date] = None
    semester_end: Optional[date] = None
    exam_date: Optional[datetime] = None
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

    @classmethod
    def from_domain(cls, course: 'Course') -> 'CourseResponse':
        return cls(
            id=course.id,
            user_id=course.user_id,
            title=course.title,
            subject=course.subject,
            description=course.description,
            semester_start=course.semester_start,
            semester_end=course.semester_end,
            exam_date=course.exam_date,
            is_archived=course.is_archived,
            created_at=course.created_at,
            updated_at=course.updated_at,
            stats=CourseStats(
                exam_count=course.exam_count,
                topic_count=course.topic_count,
                completed_topics=course.completed_topics,
                due_flashcards_count=course.due_flashcards_count,
                total_actual_study_minutes=course.total_actual_study_minutes,
                total_planned_study_minutes=course.total_planned_study_minutes,
                average_difficulty=course.average_difficulty,
                progress_percentage=course.get_progress_percentage()
            )
        )

class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
