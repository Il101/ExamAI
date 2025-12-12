from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_current_active_user, get_db
from app.domain.user import User
from app.repositories.quiz_result_repository import QuizResultRepository
from app.schemas.quiz_result import (
    QuizResultCreate,
    QuizResultResponse,
    QuizStatsResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


def get_quiz_result_repo(db: AsyncSession = Depends(get_db)) -> QuizResultRepository:
    """Dependency to get quiz result repository"""
    return QuizResultRepository(db)


@router.post("/", response_model=QuizResultResponse, status_code=status.HTTP_201_CREATED)
async def submit_quiz_result(
    request: QuizResultCreate,
    current_user: User = Depends(get_current_active_user),
    repo: QuizResultRepository = Depends(get_quiz_result_repo),
):
    """
    Submit a quiz result.
    
    Records the completion of an MCQ quiz for analytics tracking.
    """
    result = await repo.create_result(
        user_id=current_user.id,
        topic_id=request.topic_id,
        questions_total=request.questions_total,
        questions_correct=request.questions_correct,
    )

    return QuizResultResponse.from_orm(result)


@router.get("/stats", response_model=QuizStatsResponse)
async def get_quiz_stats(
    current_user: User = Depends(get_current_active_user),
    repo: QuizResultRepository = Depends(get_quiz_result_repo),
):
    """Get aggregate quiz statistics for the current user"""
    stats = await repo.get_user_stats(current_user.id)
    return QuizStatsResponse(**stats)


@router.get("/recent", response_model=List[QuizResultResponse])
async def get_recent_results(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    repo: QuizResultRepository = Depends(get_quiz_result_repo),
):
    """Get recent quiz results for the current user"""
    results = await repo.get_recent_results(current_user.id, limit=limit)
    return [QuizResultResponse.from_orm(r) for r in results]


@router.get("/topic/{topic_id}", response_model=List[QuizResultResponse])
async def get_topic_results(
    topic_id: UUID,
    current_user: User = Depends(get_current_active_user),
    repo: QuizResultRepository = Depends(get_quiz_result_repo),
):
    """Get all quiz results for a specific topic"""
    results = await repo.get_topic_results(topic_id)
    return [QuizResultResponse.from_orm(r) for r in results]
