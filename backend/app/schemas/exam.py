from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.schemas.topic import TopicResponse


class ExamCreate(BaseModel):
    """Create exam request"""

    title: str = Field(..., min_length=3, max_length=500)
    subject: str = Field(..., min_length=2, max_length=200)
    exam_type: str = Field(..., pattern="^(oral|written|test)$")
    level: str = Field(..., pattern="^(school|bachelor|master|phd)$")
    original_content: str = Field(..., min_length=100)

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Calculus I Midterm",
                "subject": "Mathematics",
                "exam_type": "written",
                "level": "bachelor",
                "original_content": "Chapter 1: Limits and Continuity...",
            }
        }


class ExamUpdate(BaseModel):
    """Update exam request"""

    title: Optional[str] = Field(None, min_length=3, max_length=500)
    subject: Optional[str] = Field(None, min_length=2, max_length=200)


class ExamResponse(BaseModel):
    """Exam response"""

    id: UUID
    user_id: UUID
    title: str
    subject: str
    exam_type: str
    level: str
    status: str
    topic_count: int
    completed_topics: int = 0
    due_flashcards_count: int = 0
    total_actual_study_minutes: int = 0
    created_at: datetime
    updated_at: datetime

    # Optional fields (only if ready)
    ai_summary: Optional[str] = None
    token_count_input: Optional[int] = None
    token_count_output: Optional[int] = None
    generation_cost_usd: Optional[float] = None
    plan_data: Optional[dict] = None  # JSON plan data
    topics: List["TopicResponse"] = []  # Related topics

    class Config:
        from_attributes = True


class ExamListResponse(BaseModel):
    """List of exams response"""

    exams: list[ExamResponse]
    total: int
    limit: int
    offset: int


class StartGenerationRequest(BaseModel):
    """Start exam generation request"""

    # Empty for now, may add options later


class GenerationStatusResponse(BaseModel):
    """Generation status response"""

    exam_id: UUID
    status: str
    progress: float  # 0.0 to 1.0
    current_step: Optional[str] = None
    total_steps: Optional[int] = None
    completed_steps: Optional[int] = None


# Resolve forward references
if not TYPE_CHECKING:
    from app.schemas.topic import TopicResponse  # noqa: F811

    ExamResponse.model_rebuild()
