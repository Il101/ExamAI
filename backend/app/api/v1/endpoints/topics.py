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


@router.post("/{topic_id}/view", response_model=dict)
async def on_topic_viewed(
    topic_id: UUID,
    exam_id: UUID = Query(..., description="Exam ID"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Trigger next block generation when user views topic (v3.0).
    
    This endpoint:
    1. Checks if current topic is last in its block
    2. If yes, triggers generation of next block
    3. Returns status
    
    Used for progressive generation to avoid generating all topics upfront.
    """
    from app.api.dependencies import get_generation_service
    from app.repositories.exam_repository import ExamRepository
    from app.agent.schemas import ExamPlan
    
    # Get exam
    exam_repo = ExamRepository(session)
    exam = await exam_repo.get_by_id(exam_id)
    
    if not exam or exam.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Check if exam has plan_data
    if not exam.plan_data:
        return {"message": "Exam does not have v3.0 plan", "triggered": False}
    
    try:
        # Parse plan
        plan = ExamPlan.model_validate(exam.plan_data)
        
        # Trigger next block if needed
        generation_service = get_generation_service()
        await generation_service.trigger_next_block(
            exam_id=exam.id,
            current_topic_id=str(topic_id),
            plan=plan,
            cache_name=exam.cache_name
        )
        
        return {
            "message": "Topic viewed",
            "topic_id": str(topic_id),
            "triggered": True
        }
    
    except Exception as e:
        return {
            "message": f"Failed to trigger next block: {str(e)}",
            "triggered": False
        }
