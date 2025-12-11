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

    quality: int = Field(..., ge=1, le=4, description="Rating: 1=Again, 2=Hard, 3=Good, 4=Easy")


class IntervalsPreviewResponse(BaseModel):
    """Preview of next review intervals for all rating options"""
    
    again: int = Field(..., description="Interval if rated 'Again' (minutes or days)")
    hard: int = Field(..., description="Interval if rated 'Hard' (minutes or days)")
    good: int = Field(..., description="Interval if rated 'Good' (minutes or days)")
    easy: int = Field(..., description="Interval if rated 'Easy' (minutes or days)")


class ReviewStatsResponse(BaseModel):
    """Review statistics response"""

    total_reviews: int
    success_rate: float
    items_due: int
    items_learned: int
    streak_days: int
