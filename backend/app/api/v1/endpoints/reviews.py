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
    IntervalsPreviewResponse,
)
from app.services.study_service import StudyService

router = APIRouter()


@router.get("/due", response_model=List[ReviewItemResponse])
async def get_due_reviews(
    limit: int = Query(20, ge=1, le=100),
    exam_id: UUID | None = Query(None),
    topic_id: UUID | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """
    Get review items due for study.

    Returns items scheduled for review today, ordered by priority.
    """

    items = await study_service.get_due_reviews(
        user_id=current_user.id, 
        limit=limit,
        exam_id=exam_id,
        topic_id=topic_id
    )

    return [ReviewItemResponse.from_orm(item) for item in items]


@router.get("/{review_id}/intervals", response_model=IntervalsPreviewResponse)
async def get_intervals_preview(
    review_id: UUID,
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """
    Get preview of next review intervals for all rating options.
    
    Shows user how their rating choice will affect the next review schedule.
    """
    try:
        intervals = await study_service.get_next_intervals_preview(
            user_id=current_user.id,
            review_item_id=review_id
        )
        return IntervalsPreviewResponse(**intervals)
    except ValueError:
        raise NotFoundException("Review item", str(review_id))


@router.post("/{review_id}/submit", response_model=ReviewItemResponse)
async def submit_review(
    review_id: UUID,
    request: SubmitReviewRequest,
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """
    Submit review response.

    - **quality**: Rating 1-4 (1=Again, 2=Hard, 3=Good, 4=Easy)

    Updates FSRS algorithm and schedules next review.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"submit_review called: review_id={review_id}, user_id={current_user.id}, quality={request.quality}")

    try:
        item = await study_service.submit_review(
            user_id=current_user.id, review_item_id=review_id, quality=request.quality
        )
        logger.info(f"submit_review success: review_id={review_id}")
        return ReviewItemResponse.from_orm(item)

    except ValueError as e:
        logger.error(f"submit_review failed: review_id={review_id}, error={e}")
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
