from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import (
    get_auth_service,
    get_current_active_user,
    get_exam_repo,
    get_review_repo,
    get_study_session_repo,
    get_subscription_repo,
)
from app.domain.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.study_session_repository import StudySessionRepository
from app.repositories.subscription_repository import SubscriptionRepository
from app.schemas.user import ChangePasswordRequest, UserResponse, UserUpdateRequest
from app.services.auth_service import AuthService

router = APIRouter()


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Update user profile"""
    try:
        updated_user = await auth_service.update_profile(
            user_id=current_user.id,
            full_name=request.full_name,
            daily_study_goal_minutes=request.daily_study_goal_minutes,
            preferred_language=request.preferred_language,
            timezone=request.timezone,
            notification_exam_ready=request.notification_exam_ready,
            notification_study_reminders=request.notification_study_reminders,
            notification_product_updates=request.notification_product_updates,
        )
        return UserResponse.from_orm(updated_user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Change password"""
    try:
        await auth_service.change_password(
            current_password=request.current_password, new_password=request.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me/export")
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    exam_repo: ExamRepository = Depends(get_exam_repo),
    review_repo: ReviewItemRepository = Depends(get_review_repo),
    session_repo: StudySessionRepository = Depends(get_study_session_repo),
    subscription_repo: SubscriptionRepository = Depends(get_subscription_repo),
    db: AsyncSession = Depends(get_db),
):
    """
    Export all user data (GDPR compliance).
    
    Returns a JSON file with all user data including:
    - Profile information
    - Exams and topics
    - Review items
    - Study sessions
    - Subscription information
    """
    try:
        # Collect all user data
        data: Dict[str, Any] = {
            "export_date": datetime.now(timezone.utc).isoformat(),
            "user": {
                "id": str(current_user.id),
                "email": current_user.email,
                "full_name": current_user.full_name,
                "role": current_user.role,
                "subscription_tier": current_user.subscription_tier,
                "daily_study_goal_minutes": current_user.daily_study_goal_minutes,
                "preferred_language": current_user.preferred_language,
                "timezone": current_user.timezone,
                "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
                "updated_at": current_user.updated_at.isoformat() if current_user.updated_at else None,
            },
            "exams": [],
            "review_items": [],
            "study_sessions": [],
            "subscription": None,
        }

        # Get exams with topics
        exams = await exam_repo.list_by_user(current_user.id, limit=1000)
        for exam in exams:
            exam_data = {
                "id": str(exam.id),
                "title": exam.title,
                "subject": exam.subject,
                "exam_type": exam.exam_type,
                "level": exam.level,
                "status": exam.status,
                "created_at": exam.created_at.isoformat() if exam.created_at else None,
                "topics": [],
            }
            
            # Get topics for this exam
            from app.repositories.topic_repository import TopicRepository
            topic_repo = TopicRepository(db)
            topics = await topic_repo.get_by_exam_id(exam.id)
            
            for topic in topics:
                exam_data["topics"].append({
                    "id": str(topic.id),
                    "topic_name": topic.topic_name,
                    "content": topic.content,
                    "order_index": topic.order_index,
                    "difficulty_level": topic.difficulty_level,
                    "estimated_study_minutes": topic.estimated_study_minutes,
                })
            
            data["exams"].append(exam_data)

        # Get review items
        reviews = await review_repo.get_by_user(current_user.id, limit=10000)
        for review in reviews:
            data["review_items"].append({
                "id": str(review.id),
                "topic_id": str(review.topic_id),
                "difficulty": review.difficulty,
                "stability": review.stability,
                "due_date": review.due_date.isoformat() if review.due_date else None,
                "last_review": review.last_review.isoformat() if review.last_review else None,
                "review_count": review.review_count,
            })

        # Get study sessions
        sessions = await session_repo.get_by_user(current_user.id, limit=1000)
        for session in sessions:
            data["study_sessions"].append({
                "id": str(session.id),
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "cards_reviewed": session.cards_reviewed,
                "correct_count": session.correct_count,
            })

        # Get subscription
        subscription = await subscription_repo.get_by_user_id(current_user.id)
        if subscription:
            data["subscription"] = {
                "id": str(subscription.id),
                "tier": subscription.tier,
                "status": subscription.status,
                "current_period_start": subscription.current_period_start.isoformat() if subscription.current_period_start else None,
                "current_period_end": subscription.current_period_end.isoformat() if subscription.current_period_end else None,
                "cancel_at_period_end": subscription.cancel_at_period_end,
            }

        # Return as downloadable JSON
        return JSONResponse(
            content=data,
            headers={
                "Content-Disposition": f'attachment; filename="examai_data_export_{current_user.id}.json"'
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export data: {str(e)}",
        )


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Delete the current user's account.
    
    This will:
    1. Delete the user from Supabase Auth
    2. Delete the user from the local database
    3. Remove all associated data (cascading delete)
    """
    try:
        await auth_service.delete_user(current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
