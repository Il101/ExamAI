from fastapi import APIRouter, Depends, Query
from uuid import UUID
from typing import List

from app.schemas.topic import TopicResponse
from app.repositories.topic_repository import TopicRepository
from app.dependencies import get_current_active_user, get_topic_repo
from app.domain.user import User
from app.core.exceptions import NotFoundException

router = APIRouter()

@router.get("/", response_model=List[TopicResponse])
async def list_topics(
    exam_id: UUID = Query(..., description="Exam ID to filter topics"),
    current_user: User = Depends(get_current_active_user),
    topic_repo: TopicRepository = Depends(get_topic_repo)
):
    """
    List topics for an exam.
    """
    # TODO: Check if user owns the exam
    
    topics = await topic_repo.get_by_exam_id(exam_id)
    return [TopicResponse.from_orm(t) for t in topics]

