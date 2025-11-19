from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.db.session import get_db
from app.dependencies import (get_agent_service, get_current_active_user,
                              get_exam_service)
from app.domain.user import User
from app.repositories.topic_repository import TopicRepository
from app.schemas.exam import (ExamCreate, ExamListResponse, ExamResponse,
                              ExamUpdate, GenerationStatusResponse,
                              StartGenerationRequest)
from app.schemas.topic import TopicResponse
from app.services.agent_service import AgentService
from app.services.exam_service import ExamService
from app.tasks.exam_tasks import generate_exam_content

router = APIRouter()


@router.post("/", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    request: ExamCreate,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """
    Create new exam.

    Creates exam in 'draft' status. Use /exams/{id}/generate to start AI generation.
    """

    try:
        exam = await exam_service.create_exam(
            user=current_user,
            title=request.title,
            subject=request.subject,
            exam_type=request.exam_type,
            level=request.level,
            original_content=request.original_content,
        )

        return ExamResponse.from_orm(exam)

    except ValueError as e:
        raise ValidationException(str(e))


@router.get("/", response_model=ExamListResponse)
async def list_exams(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """
    List user's exams.

    - **status**: Filter by status (draft, generating, ready, failed, archived)
    - **limit**: Maximum number of results
    - **offset**: Pagination offset
    """

    exams = await exam_service.list_user_exams(
        user_id=current_user.id, status=status, limit=limit, offset=offset
    )

    total = await exam_service.exam_repo.count_by_user(current_user.id, status)

    return ExamListResponse(
        exams=[ExamResponse.from_orm(exam) for exam in exams],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{exam_id}", response_model=ExamResponse)
async def get_exam(
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
    db: AsyncSession = Depends(get_db),
):
    """Get exam by ID with topics"""

    exam = await exam_service.get_exam(current_user.id, exam_id)

    if not exam:
        raise NotFoundException("Exam", str(exam_id))

    # Load topics
    topic_repo = TopicRepository(db)
    topics = await topic_repo.get_by_exam_id(exam_id)

    # Build response
    response = ExamResponse.from_orm(exam)
    response.topics = [
        TopicResponse(
            id=t.id,
            exam_id=t.exam_id,
            topic_name=t.topic_name,
            content=t.content,
            order_index=t.order_index,
            difficulty_level=t.difficulty_level,
            estimated_study_minutes=t.estimated_study_minutes,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in topics
    ]

    return response


@router.patch("/{exam_id}", response_model=ExamResponse)
async def update_exam(
    exam_id: UUID,
    request: ExamUpdate,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """Update exam details"""

    exam = await exam_service.update_exam(
        user_id=current_user.id,
        exam_id=exam_id,
        updates=request.dict(exclude_unset=True),
    )

    if not exam:
        raise NotFoundException("Exam", str(exam_id))

    return ExamResponse.from_orm(exam)


@router.delete("/{exam_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exam(
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """Delete exam"""

    success = await exam_service.delete_exam(current_user.id, exam_id)

    if not success:
        raise NotFoundException("Exam", str(exam_id))


@router.post("/{exam_id}/generate", response_model=dict)
async def generate_exam_content_endpoint(
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """
    Start AI content generation for exam (async with Celery).

    Returns task ID to poll for progress.
    """

    # Verify exam exists and belongs to user
    exam = await exam_service.get_exam(current_user.id, exam_id)
    if not exam:
        raise NotFoundException("Exam", str(exam_id))

    # Check if can generate
    if not exam.can_generate():
        raise ValidationException(f"Cannot generate exam with status: {exam.status}")

    # Mark as generating
    exam.start_generation()
    await exam_service.exam_repo.update(exam)

    # Start Celery task
    task = generate_exam_content.delay(
        exam_id=str(exam_id), user_id=str(current_user.id)
    )

    return {
        "task_id": task.id,
        "status": "Task started",
        "message": "Exam generation in progress. Poll /tasks/{task_id} for status.",
    }


@router.get("/{exam_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    agent_service: AgentService = Depends(get_agent_service),
):
    """Get generation status"""

    status_data = await agent_service.get_status(current_user.id, exam_id)

    if not status_data:
        raise NotFoundException("Exam", str(exam_id))

    return GenerationStatusResponse(**status_data)
