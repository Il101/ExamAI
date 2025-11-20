from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.dependencies import get_current_admin, get_db, get_user_repo, get_exam_repo
from app.domain.user import User
from app.services.admin_service import AdminService
from app.repositories.user_repository import UserRepository
from app.repositories.exam_repository import ExamRepository
from app.schemas.admin import (
    AdminUserResponse,
    UserListResponse,
    AdminUserUpdate,
    SystemStatistics,
    AdminExamResponse,
    ExamListResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


async def get_admin_service(
    session: AsyncSession = Depends(get_db),
    user_repo: UserRepository = Depends(get_user_repo),
    exam_repo: ExamRepository = Depends(get_exam_repo),
) -> AdminService:
    """Get admin service"""
    return AdminService(session, user_repo, exam_repo)


@router.get("/users", response_model=UserListResponse)
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    List all users (admin only).

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    users, total = await admin_service.list_all_users(skip, limit)

    return UserListResponse(
        users=[AdminUserResponse.from_orm(user) for user in users],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Get specific user details (admin only)"""
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return AdminUserResponse.from_orm(user)


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: UUID,
    update_data: AdminUserUpdate,
    current_admin: User = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """
    Update user (admin only).

    Can update: role, subscription_plan, is_verified
    """
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    if update_data.role is not None:
        user.role = update_data.role
    if update_data.subscription_plan is not None:
        user.subscription_plan = update_data.subscription_plan
    if update_data.is_verified is not None:
        user.is_verified = update_data.is_verified

    updated_user = await user_repo.update(user)

    return AdminUserResponse.from_orm(updated_user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    user_repo: UserRepository = Depends(get_user_repo),
):
    """Delete user (admin only)"""
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent deleting yourself
    if user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await user_repo.delete(user_id)

    return None


@router.get("/statistics", response_model=SystemStatistics)
async def get_statistics(
    current_admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get system-wide statistics (admin only)"""
    return await admin_service.get_system_statistics()


@router.get("/exams", response_model=ExamListResponse)
async def list_exams(
    skip: int = 0,
    limit: int = 50,
    current_admin: User = Depends(get_current_admin),
    admin_service: AdminService = Depends(get_admin_service),
):
    """
    List all exams across all users (admin only).

    - **skip**: Number of records to skip
    - **limit**: Maximum number of records to return
    """
    exams, total = await admin_service.list_all_exams(skip, limit)

    return ExamListResponse(
        exams=[AdminExamResponse(**exam) for exam in exams],
        total=total,
        skip=skip,
        limit=limit,
    )
