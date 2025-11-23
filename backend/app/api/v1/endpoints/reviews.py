from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.exceptions import NotFoundException
from app.dependencies import get_current_active_user, get_study_service
from app.domain.user import User
from app.schemas.review import (
    ReviewItemResponse,
    ReviewStatsResponse,
    SubmitReviewRequest,
)
from app.services.study_service import StudyService

router = APIRouter()


@router.get("/due", response_model=List[ReviewItemResponse])
async def get_due_reviews(
    limit: int = Query(20, ge=1, le=100),
    interleave: bool = Query(True, description="Mix topics for better retention"),
    topic_mix_count: int = Query(3, ge=2, le=10, description="Number of topics to mix"),
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """
    Get review items due for study.

    Returns items scheduled for review today, ordered by priority.
    Supports interleaved practice by mixing topics.
    """

    items = await study_service.get_due_reviews(
        current_user.id, 
        limit, 
        interleave=interleave,
        topic_mix_count=topic_mix_count
    )

    return [ReviewItemResponse.from_orm(item) for item in items]


@router.post("/{review_id}/submit", response_model=ReviewItemResponse)
async def submit_review(
    review_id: UUID,
    request: SubmitReviewRequest,
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """
    Submit review response.

    - **quality**: Rating 0-5 (0=blackout, 5=perfect recall)

    Updates SM-2 algorithm and schedules next review.
    """

    try:
        item = await study_service.submit_review(
            user_id=current_user.id, review_item_id=review_id, quality=request.quality
        )

        return ReviewItemResponse.from_orm(item)

    except ValueError:
        raise NotFoundException("Review item", str(review_id))


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_statistics(
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """
    Get user's review statistics.

    Returns total reviews, success rate, items due, etc.
    """

    stats = await study_service.get_study_statistics(current_user.id)

    return ReviewStatsResponse(**stats)
