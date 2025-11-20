from fastapi import APIRouter, Depends

from app.dependencies import get_current_active_user, get_study_service
from app.domain.user import User
from app.schemas.analytics import AnalyticsResponse
from app.services.study_service import StudyService

router = APIRouter()


@router.get("/dashboard", response_model=AnalyticsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """Get dashboard statistics"""
    return await study_service.get_analytics(current_user.id)
