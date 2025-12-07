from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.rate_limit import dynamic_rate_limit
from app.db.session import get_db
from app.dependencies import (
    get_agent_service,
    get_current_active_user,
    get_exam_service,
    get_llm_provider,
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
from app.integrations.llm.base import LLMProvider
from app.tasks.exam_tasks import generate_exam_content
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
async def create_exam(
    request: ExamCreate,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """
    Create a new exam (legacy endpoint).
    
    Note: This endpoint is deprecated. Use POST /v3 instead.
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
    title: str = Form(...),
    subject: str = Form(...),
    exam_type: str = Form(...),
    level: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
    llm_provider: LLMProvider = Depends(get_llm_provider),
):
    """
    Create exam with automatic plan generation and caching (v3.0).
    
    This endpoint:
    1. Accepts file upload (PDF, DOCX, TXT, MP3, MP4)
    2. Extracts content using Gemini File API
    3. Creates exam with generated plan
    4. Creates Gemini cache and uploads to S3
    5. Triggers prefetch for first 2 topics
    6. Returns exam with plan
    
    Rate limits:
    - Free tier: 50 requests/hour
    - Pro tier: 500 requests/hour
    - Premium tier: Unlimited
    """
    from app.services.exam_creation_v3 import create_exam_with_plan
    from app.agent.cached_planner import CachedCoursePlanner
    from app.integrations.llm.gemini import GeminiProvider
    from app.api.dependencies import (
        get_storage, get_cache_manager, get_generation_service
    )
    from app.core.config import settings
    from google.genai import types
    import tempfile
    import os
    
    tmp_path = None
    pdf_path = None
    warnings = []
    
    try:
        # Validate file size (10MB limit)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        content_bytes = await file.read()
        
        if len(content_bytes) > MAX_FILE_SIZE:
            raise ValidationException("File too large. Maximum size is 10MB.")
        
        # Validate file type
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "audio/mpeg",
            "video/mp4",
        ]
        
        if file.content_type not in allowed_types:
            raise ValidationException(
                f"Unsupported file type: {file.content_type}. "
                "Supported types: PDF, DOCX, TXT, MP3, MP4"
            )
        
        # Create temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            tmp.write(content_bytes)
            tmp_path = tmp.name
        
        # Get Gemini client
        client = llm_provider.client
        
        # 1. Upload to Gemini (for Context Caching)
        uploaded_file = client.files.upload(file=tmp_path, config={'mime_type': file.content_type})
        gemini_file_uri = uploaded_file.uri
        logger.info(f"Uploaded file '{file.filename}' ({file.content_type}) to Gemini: {gemini_file_uri}")
        
        # 2. Upload to Supabase Storage (Source of Truth)
        storage_path = None
        media_supported_types = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        
        # We process all supported media types by uploading separate copy to storage
        if file.content_type in media_supported_types:
            try:
                # Ensure we have a PDF (or keep docx if supported by storage viewer, but PDF is safer)
                # For now, let's just upload the raw file as is or convert if needed
                # The 'ensure_pdf' utility is good for standardizing
                from app.utils.pdf_converter import ensure_pdf
                pdf_path = ensure_pdf(tmp_path, file.content_type)
                
                # Upload PDF to storage
                filename = f"{uuid4()}.pdf"
                storage_path = f"exams/source/{filename}"
                
                with open(pdf_path, "rb") as f:
                    file_data = f.read()
                    await get_storage().upload_file(file_data, storage_path)
                    
                logger.info(f"Successfully processed and stored source file: {storage_path}")
                
            except Exception as e:
                logger.error(f"Source file upload failed: {e}", exc_info=True)
                warnings.append("Failed to backup source file.")

        # 3. Extract text from file for AI processing
        # NOTE: We don't extract text anymore - file is processed via Gemini Files API
        # Setting original_content to empty when file is uploaded
        original_content = ""  # Content is in gemini_file_uri, not extracted text
        
        # Initialize services
        llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        planner = CachedCoursePlanner(llm_provider=llm)
        store = get_storage()
        cache_manager = get_cache_manager()
        gen_service = get_generation_service()
        
        # Create exam with plan
        # Note: 'gemini_file_uri' is passed so Planner will create cache from it directly
        exam, plan = await create_exam_with_plan(
            exam_service=exam_service,
            user=current_user,
            title=title,
            subject=subject,
            exam_type=exam_type,
            level=level,
            original_content=original_content,
            planner=planner,
            storage=store,
            cache_manager=cache_manager,
            generation_service=gen_service,
            original_file_url=storage_path,
            original_file_mime_type="application/pdf" if file.content_type in media_supported_types else file.content_type,
            gemini_file_uri=gemini_file_uri
        )
        
        # DO NOT delete Gemini file - it's needed for cache creation and potential recreation
        # Gemini files auto-expire after 48 hours, so no manual cleanup needed
        # Keeping the file ensures:
        # 1. Cache can be created successfully during plan generation
        # 2. Cache can be recreated if it expires during long-running operations
        # 3. No "File not found" errors during async cache operations
        # if uploaded_file:
        #     try:
        #         client.files.delete(name=uploaded_file.name)
        #     except Exception as e:
        #         logger.warning(f"Failed to delete Gemini file {uploaded_file.name}: {e}")

        # Trigger Async Text Extraction
        try:
            from app.tasks.exam_tasks import extract_exam_content
            extract_exam_content.delay(str(exam.id))
            logger.info(f"Triggered background text extraction for exam {exam.id}")
        except Exception as e:
            logger.error(f"Failed to trigger extraction task: {e}")
            
        # Save Metadata for File-Based Cache Recovery
        if storage_path:
            try:
                import json
                meta = {
                    "url": storage_path,
                    "mime_type": "application/pdf" if file.content_type in media_supported_types else file.content_type
                }
                await store.upload_file(
                    json.dumps(meta).encode('utf-8'),
                    f"exams/{exam.id}/source_meta.json"
                )
                logger.info(f"Saved recovery metadata for exam {exam.id}")
            except Exception as e:
                logger.warning(f"Failed to save recovery metadata: {e}")

        response_data = {
            "exam": ExamResponse.model_validate(exam).model_dump(),
            "plan": plan.model_dump(),
            "message": "Exam created with plan. Content will be indexed in background."
        }
        
        if warnings:
            response_data["warnings"] = warnings
            
        return response_data

    except ValueError as e:
        raise ValidationException(str(e))
    
    finally:
        # Guaranteed cleanup of all temp files
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
                logger.debug(f"Cleaned up temp file: {tmp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {tmp_path}: {e}")
        
        if 'pdf_path' in locals() and pdf_path and pdf_path != tmp_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
                logger.debug(f"Cleaned up PDF file: {pdf_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup PDF file {pdf_path}: {e}")




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
