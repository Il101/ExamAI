from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.core.exceptions import NotFoundException
from app.dependencies import get_current_active_user, get_study_service
from app.domain.user import User
from app.schemas.study_session import StudySessionCreate, StudySessionResponse
from app.services.study_service import StudyService

router = APIRouter()


@router.post(
    "/", response_model=StudySessionResponse, status_code=status.HTTP_201_CREATED
)
async def start_session(
    request: StudySessionCreate,
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """Start a new study session"""
    session = await study_service.start_study_session(
        user_id=current_user.id,
        exam_id=request.exam_id,
        pomodoro_duration=request.duration_minutes,
    )
    return StudySessionResponse.from_orm(session)


@router.post("/{session_id}/end", response_model=StudySessionResponse)
async def end_session(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """End a study session"""
    session = await study_service.end_study_session(
        user_id=current_user.id, session_id=session_id
    )
    if not session:
        raise NotFoundException("Study session", str(session_id))
    return StudySessionResponse.from_orm(session)


@router.post("/{session_id}/pomodoro", response_model=StudySessionResponse)
async def complete_pomodoro(
    session_id: UUID,
    current_user: User = Depends(get_current_active_user),
    study_service: StudyService = Depends(get_study_service),
):
    """Complete a pomodoro interval"""
    session = await study_service.complete_pomodoro(
        user_id=current_user.id, session_id=session_id
    )
    return StudySessionResponse.from_orm(session)
