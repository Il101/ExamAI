from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse, UserUpdateRequest, ChangePasswordRequest
from app.dependencies import get_current_active_user
from app.domain.user import User

router = APIRouter()


@router.patch("/me", response_model=UserResponse)
async def update_user_profile(
    request: UserUpdateRequest, current_user: User = Depends(get_current_active_user)
):
    """Update user profile"""
    # TODO: Implement update logic in AuthService or UserRepository
    return UserResponse.from_orm(current_user)


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
):
    """Change password"""
    # TODO: Implement change password logic
    return {"message": "Password changed successfully"}
