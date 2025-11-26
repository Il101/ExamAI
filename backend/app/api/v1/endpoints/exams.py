from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.rate_limit import dynamic_rate_limit
from app.db.session import get_db
from app.dependencies import (
    get_agent_service,
    get_current_active_user,
    get_exam_service,
)
from app.domain.user import User
from app.repositories.topic_repository import TopicRepository
from app.schemas.exam import (
    ExamCreate,
    ExamListResponse,
    ExamResponse,
    ExamUpdate,
    GenerationStatusResponse,
)
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
    
    Rate limits:
    - Free tier: 100 requests/hour
    - Pro tier: 1000 requests/hour
    - Premium tier: Unlimited
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

        return ExamResponse.model_validate(exam)

    except ValueError as e:
        raise ValidationException(str(e))


@router.post("/v3", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_exam_v3(
    request: ExamCreate,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """
    Create exam with automatic plan generation and caching (v3.0).
    
    This endpoint:
    1. Creates exam
    2. Generates plan with blocks
    3. Creates Gemini cache and uploads to S3
    4. Triggers prefetch for first 2 topics
    5. Returns exam with plan
    
    Rate limits:
    - Free tier: 50 requests/hour
    - Pro tier: 500 requests/hour
    - Premium tier: Unlimited
    """
    from app.services.exam_creation_v3 import create_exam_with_plan
    from app.agent.cached_planner import CachedCoursePlanner
    from app.integrations.llm.gemini_provider import GeminiProvider
    from app.api.dependencies import (
        get_storage, get_cache_manager, get_generation_service
    )
    from app.core.config import settings
    
    try:
        # Initialize services
        llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        planner = CachedCoursePlanner(llm)
        storage = get_storage()
        cache_manager = get_cache_manager()
        generation_service = get_generation_service()
        
        # Create exam with plan
        exam, plan = await create_exam_with_plan(
            exam_service=exam_service,
            user=current_user,
            title=request.title,
            subject=request.subject,
            exam_type=request.exam_type,
            level=request.level,
            original_content=request.original_content,
            planner=planner,
            storage=storage,
            cache_manager=cache_manager,
            generation_service=generation_service
        )
        
        return {
            "exam": ExamResponse.model_validate(exam).model_dump(),
            "plan": plan.model_dump(),
            "message": "Exam created with plan. First 2 topics are being generated."
        }
    
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
        exams=[ExamResponse.model_validate(exam) for exam in exams],
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
    response = ExamResponse.model_validate(exam)
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
        updates=request.model_dump(exclude_unset=True),
    )

    if not exam:
        raise NotFoundException("Exam", str(exam_id))

    return ExamResponse.model_validate(exam)


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
    
    Automatically handles both draft and planned exams:
    - If exam is in 'draft' status: creates plan first, then generates content
    - If exam is in 'planned' status: directly generates content
    
    Returns task ID to poll for progress.
    """
    from app.tasks.exam_tasks import create_exam_plan, generate_exam_content
    from celery import chain
    
    try:
        # Get exam to check status
        exam = await exam_service.get_exam(current_user.id, exam_id)
        if not exam:
            raise NotFoundException("Exam", str(exam_id))
        
        # Handle based on current status
        if exam.status == "draft":
            # Need to create plan first, then generate content
            # Start planning
            exam.start_planning()
            await exam_service.exam_repo.update(exam)
            
            # Create task chain: plan -> generate
            task_chain = chain(
                create_exam_plan.s(exam_id=str(exam_id), user_id=str(current_user.id)),
                generate_exam_content.si(exam_id=str(exam_id), user_id=str(current_user.id)),
            )
            task = task_chain.apply_async()
            
            return {
                "task_id": task.id,
                "status": "Planning and generation started",
                "message": "Creating plan and generating content. Poll /tasks/{task_id} for status.",
            }
            
        elif exam.status == "planned":
            # Already has plan, just generate content
            updated_exam, task_id = await exam_service.start_generation(
                user_id=current_user.id, exam_id=exam_id
            )
            return {
                "task_id": task_id,
                "status": "Generation started",
                "message": "Generating content. Poll /tasks/{task_id} for status.",
            }
        else:
            raise ValidationException(f"Cannot generate exam with status: {exam.status}")
            
    except ValueError as e:
         if "not found" in str(e).lower():
             raise NotFoundException("Exam", str(exam_id))
         raise ValidationException(str(e))


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


@router.post("/{exam_id}/plan", response_model=dict)
async def create_exam_plan_endpoint(
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """
    Start AI planning phase (Step 1).
    Creates topics but does not generate content.
    """
    try:
        updated_exam, task_id = await exam_service.create_plan(
            user_id=current_user.id, exam_id=exam_id
        )
    except ValueError as e:
         if "not found" in str(e).lower():
             raise NotFoundException("Exam", str(exam_id))
         raise ValidationException(str(e))

    return {
        "task_id": task_id,
        "status": "Planning started",
        "message": "Exam planning in progress. Topics will appear shortly.",
    }
