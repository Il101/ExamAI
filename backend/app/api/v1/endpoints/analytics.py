from fastapi import APIRouter, Depends
from app.dependencies import get_current_active_user
from app.domain.user import User

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_stats(current_user: User = Depends(get_current_active_user)):
    """Get dashboard statistics"""
    return {"total_exams": 0, "study_streak": 0, "reviews_due": 0}
