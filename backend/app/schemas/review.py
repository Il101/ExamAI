from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewItemResponse(BaseModel):
    """Review item response"""

    id: UUID
    user_id: UUID
    topic_id: UUID
    question: str
    answer: str
    easiness_factor: float
    interval_days: float
    repetitions: int
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
