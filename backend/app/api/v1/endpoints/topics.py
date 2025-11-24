from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_active_user, get_topic_repo
from app.domain.user import User
from app.repositories.topic_repository import TopicRepository
from app.schemas.topic import TopicResponse

router = APIRouter()


@router.get("/", response_model=List[TopicResponse])
async def list_topics(
    exam_id: UUID = Query(..., description="Exam ID to filter topics"),
    current_user: User = Depends(get_current_active_user),
    topic_repo: TopicRepository = Depends(get_topic_repo),
):
    """
    List topics for an exam.
    """
    # TODO: Check if user owns the exam

    topics = await topic_repo.get_by_exam_id(exam_id)
    return [TopicResponse.from_orm(t) for t in topics]


@router.post("/{topic_id}/generate")
async def generate_topic(
    topic_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Generate content for a single topic (progressive generation).
    
    Triggers Celery task to generate topic content + flashcards.
    """
    from app.tasks.exam_tasks import generate_topic_content
    
    topic_repo = TopicRepository(session)
    topic = await topic_repo.get_by_id(topic_id)
    
    if not topic or topic.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    if not topic.can_generate():
        raise HTTPException(
            status_code=400,
            detail=f"Cannot generate topic with status: {topic.status}"
        )
    
    # Mark as generating
    topic.start_generation()
    await topic_repo.update(topic)
    await session.commit()
    
    # Trigger background task
    task = generate_topic_content.delay(
        topic_id=str(topic_id),
        user_id=str(current_user.id)
    )
    
    return {
        "message": "Topic generation started",
        "task_id": task.id,
        "topic_id": str(topic_id),
        "status": topic.status
    }


@router.get("/{topic_id}", response_model=TopicResponse)
async def get_topic(
    topic_id: UUID,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """Get topic with current status and content"""
    topic_repo = TopicRepository(session)
    topic = await topic_repo.get_by_id(topic_id)
    
    if not topic or topic.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    return TopicResponse.from_orm(topic)
