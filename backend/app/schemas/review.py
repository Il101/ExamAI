from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewItemResponse(BaseModel):
    """Review item response"""

    id: UUID
    user_id: UUID
    topic_id: UUID
    question: str
    answer: str
    stability: float  # FSRS: days to 90% retention
    difficulty: float  # FSRS: 0-10 scale
    scheduled_days: int  # FSRS: scheduled interval
    reps: int  # Total review count
    lapses: int  # Number of failures
    state: str  # Card state: new, learning, review, relearning
    next_review_date: datetime

    class Config:
        from_attributes = True


class SubmitReviewRequest(BaseModel):
    """Submit review request"""

    quality: int = Field(..., ge=0, le=5, description="0=blackout, 5=perfect recall")


class ReviewStatsResponse(BaseModel):
    """Review statistics response"""

    total_reviews: int
    success_rate: float
    items_due: int
    items_learned: int
    streak_days: int
