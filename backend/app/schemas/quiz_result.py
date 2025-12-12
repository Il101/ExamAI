from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class QuizResultCreate(BaseModel):
    """Request to create a quiz result"""

    topic_id: UUID
    questions_total: int = Field(..., ge=1, description="Total number of questions")
    questions_correct: int = Field(..., ge=0, description="Number of correct answers")


class QuizResultResponse(BaseModel):
    """Quiz result response"""

    id: UUID
    user_id: UUID
    topic_id: UUID
    questions_total: int
    questions_correct: int
    score_percentage: float
    completed_at: datetime
    created_at: datetime

    @classmethod
    def from_orm(cls, entity) -> "QuizResultResponse":
        """Create from domain entity"""
        return cls(
            id=entity.id,
            user_id=entity.user_id,
            topic_id=entity.topic_id,
            questions_total=entity.questions_total,
            questions_correct=entity.questions_correct,
            score_percentage=entity.score_percentage,
            completed_at=entity.completed_at,
            created_at=entity.created_at,
        )


class QuizStatsResponse(BaseModel):
    """Aggregate quiz statistics"""

    total_quizzes: int
    questions_correct: int
    questions_total: int
    average_score: float
