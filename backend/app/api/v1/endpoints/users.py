from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service, get_current_active_user
from app.domain.user import User
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
