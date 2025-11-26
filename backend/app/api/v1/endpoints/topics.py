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
    quiz_completed: bool = Query(False, description="Whether quiz was completed"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Mark topic as viewed and optionally mark quiz as completed.
    
    This endpoint:
    1. Updates is_viewed and last_viewed_at
    2. Optionally updates quiz_completed
    3. Triggers next block generation (v3.0)
    
    Used for progress tracking and progressive generation.
    """
    from datetime import datetime, timezone
    from app.api.dependencies import get_generation_service
    from app.repositories.exam_repository import ExamRepository
    from app.agent.schemas import ExamPlan
    
    topic_repo = TopicRepository(session)
    topic = await topic_repo.get_by_id(topic_id)
    
    if not topic or topic.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    # Update progress tracking
    topic.is_viewed = True
    topic.last_viewed_at = datetime.now(timezone.utc)
    
    if quiz_completed:
        topic.quiz_completed = True
    
    await topic_repo.update(topic)
    await session.commit()
    
    # Get exam for v3.0 progressive generation
    exam_repo = ExamRepository(session)
    exam = await exam_repo.get_by_id(exam_id)
    
    if not exam or exam.user_id != current_user.id:
        return {
            "message": "Topic marked as viewed",
            "topic_id": str(topic_id),
            "is_viewed": True,
            "quiz_completed": topic.quiz_completed,
            "triggered": False
        }
    
    # Check if exam has plan_data for v3.0
    if not exam.plan_data:
        return {
            "message": "Topic marked as viewed",
            "topic_id": str(topic_id),
            "is_viewed": True,
            "quiz_completed": topic.quiz_completed,
            "triggered": False
        }
    
    try:
        # Parse plan and trigger next block
        plan = ExamPlan.model_validate(exam.plan_data)
        
        generation_service = get_generation_service()
        await generation_service.trigger_next_block(
            exam_id=exam.id,
            current_topic_id=str(topic_id),
            plan=plan,
            cache_name=exam.cache_name
        )
        
        return {
            "message": "Topic marked as viewed",
            "topic_id": str(topic_id),
            "is_viewed": True,
            "quiz_completed": topic.quiz_completed,
            "triggered": True
        }
    
    except Exception as e:
        return {
            "message": "Topic marked as viewed",
            "topic_id": str(topic_id),
            "is_viewed": True,
            "quiz_completed": topic.quiz_completed,
            "triggered": False,
            "error": str(e)
        }


@router.get("/{topic_id}/quiz")
async def get_topic_quiz(
    topic_id: UUID,
    num_questions: int = Query(5, ge=1, le=10, description="Number of questions"),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_db),
):
    """
    Generate a multiple-choice quiz for a topic.
    
    Returns 5 MCQ questions based on the topic content.
    Used for "Check Yourself" interactive learning blocks.
    """
    from app.dependencies import get_llm_provider
    from app.agent.quiz_generator import QuizGenerator
    
    topic_repo = TopicRepository(session)
    topic = await topic_repo.get_by_id(topic_id)
    
    if not topic or topic.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Topic not found")
    
    if not topic.content:
        raise HTTPException(
            status_code=400,
            detail="Topic has no content yet. Cannot generate quiz."
        )
    
    try:
        # Generate quiz using AI
        llm_provider = get_llm_provider()
        quiz_gen = QuizGenerator(llm_provider)
        
        questions = await quiz_gen.generate_mcq_quiz(
            content=topic.content,
            num_questions=num_questions
        )
        
        # Convert to dict for JSON response
        return {
            "topic_id": str(topic_id),
            "topic_name": topic.topic_name,
            "questions": [
                {
                    "id": idx,
                    "question": q.question,
                    "options": [
                        {
                            "id": opt_idx,
                            "text": opt.text,
                            "is_correct": opt.is_correct
                        }
                        for opt_idx, opt in enumerate(q.options)
                    ],
                    "explanation": q.explanation
                }
                for idx, q in enumerate(questions)
            ]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quiz: {str(e)}"
        )

