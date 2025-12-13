from typing import Optional, List
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Query, Request, status, File, UploadFile, Form
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.core.rate_limit import dynamic_rate_limit
from app.db.session import get_db
from app.dependencies import (
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
from app.services.exam_service import ExamService
from app.integrations.llm.base import LLMProvider
from app.tasks.exam_tasks import generate_exam_content
import logging

logger = logging.getLogger(__name__)

router = APIRouter()



@router.post("/v3", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_exam_v3(
    title: str = Form(...),
    subject: str = Form(...),
    exam_type: str = Form(...),
    level: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
    llm_provider: LLMProvider = Depends(get_llm_provider),
):
    """
    Create exam with automatic plan generation and caching (v3.0).
    
    This endpoint:
    1. Accepts multiple file uploads (PDF, DOCX, TXT, MP3, MP4)
    2. Extracts content using Gemini File API
    3. Creates exam with generated plan
    4. Creates Gemini cache and uploads sources to storage
    5. Returns exam with plan ready for generation
    
    Rate limits:
    - Free tier: 50 requests/hour
    - Pro tier: 500 requests/hour
    - Premium tier: Unlimited
    """
    from app.services.exam_creation_v3 import create_exam_with_plan
    from app.agent.cached_planner import CachedCoursePlanner
    from app.integrations.llm.gemini import GeminiProvider
    from app.api.dependencies import (
        get_storage, get_cache_manager
    )
    from app.core.config import settings
    import tempfile
    import os
    
    import aiofiles
    
    tmp_paths: list[str] = []
    pdf_paths: list[str] = []
    warnings: list[str] = []
    gemini_files: list[dict] = []
    stored_files: list[dict] = []
    
    try:
        MAX_FILES = 5
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "audio/mpeg",
            "video/mp4",
        ]

        if len(files) > MAX_FILES:
            raise ValidationException(f"Too many files. Maximum {MAX_FILES} allowed.")

        # Get Gemini client once
        client = llm_provider.client

        for upload in files:
            # Validate file size (10MB limit)
            content_bytes = await upload.read()

            if len(content_bytes) > MAX_FILE_SIZE:
                raise ValidationException("File too large. Maximum size is 10MB per file.")

            if upload.content_type not in allowed_types:
                raise ValidationException(
                    f"Unsupported file type: {upload.content_type}. "
                    "Supported types: PDF, DOCX, TXT, MP3, MP4"
                )

            # Create temp file (async write)
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(upload.filename)[1]) as tmp:
                tmp_path = tmp.name

            tmp_paths.append(tmp_path)

            async with aiofiles.open(tmp_path, 'wb') as f:
                await f.write(content_bytes)

            # 1. Upload to Gemini (for Context Caching)
            uploaded_file = client.files.upload(file=tmp_path, config={'mime_type': upload.content_type})
            gemini_files.append({
                "uri": uploaded_file.uri,
                "mime_type": upload.content_type,
                "filename": upload.filename,
            })
            logger.info(
                f"Uploaded file '{upload.filename}' ({upload.content_type}) to Gemini: {uploaded_file.uri}"
            )

            # 2. Upload to Supabase Storage (Source of Truth)
            media_supported_types = [
                "application/pdf",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]

            storage_path = None

            if upload.content_type in media_supported_types:
                try:
                    from app.utils.pdf_converter import ensure_pdf
                    from starlette.concurrency import run_in_threadpool

                    pdf_path = await run_in_threadpool(ensure_pdf, tmp_path, upload.content_type)
                    pdf_paths.append(pdf_path)

                    filename = f"{uuid4()}.pdf"
                    storage_path = f"exams/source/{filename}"

                    async with aiofiles.open(pdf_path, "rb") as f:
                        file_data = await f.read()

                    await get_storage().upload_file(file_data, storage_path)

                    stored_files.append({
                        "storage_path": storage_path,
                        "mime_type": "application/pdf",
                        "filename": upload.filename,
                    })

                    logger.info(f"Successfully processed and stored source file: {storage_path}")

                except Exception as e:
                    logger.error(f"Source file upload failed: {e}", exc_info=True)
                    warnings.append(f"Failed to backup source file: {upload.filename}")
            else:
                stored_files.append({
                    "storage_path": None,
                    "mime_type": upload.content_type,
                    "filename": upload.filename,
                })

        if not gemini_files:
            raise ValidationException("No files uploaded")

        # 3. Extract text from file for AI processing
        original_content = ""  # Content is in Gemini Files API, not extracted text

        # Initialize services
        llm = GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
        planner = CachedCoursePlanner(llm_provider=llm)
        store = get_storage()
        cache_manager = get_cache_manager()

        # Create exam with plan (multi-file aware)
        primary_gemini_uri = gemini_files[0]["uri"] if gemini_files else None
        primary_mime = gemini_files[0]["mime_type"] if gemini_files else None

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
            original_file_url=stored_files[0].get("storage_path") if stored_files else None,
            original_file_mime_type=stored_files[0].get("mime_type") if stored_files else primary_mime,
            gemini_file_uri=primary_gemini_uri,
            original_files=stored_files,
            gemini_files=gemini_files,
        )

        # Trigger Async Content Generation
        try:
            await exam_service.exam_repo.session.commit()

            logger.info(
                f"✅ Plan created for exam {exam.id} "
                f"(cache: {exam.cache_name or 'none'}). Waiting for manual start."
            )

        except Exception as e:
            logger.error(f"Failed to trigger generation task: {e}", exc_info=True)

        # Save Metadata for File-Based Cache Recovery
        try:
            import json

            meta = []
            for idx, gf in enumerate(gemini_files):
                storage_info = stored_files[idx] if idx < len(stored_files) else {}
                meta.append({
                    "gemini_uri": gf.get("uri"),
                    "mime_type": gf.get("mime_type"),
                    "filename": gf.get("filename"),
                    "storage_path": storage_info.get("storage_path"),
                })

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
        for tmp_path in tmp_paths:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                    logger.debug(f"Cleaned up temp file: {tmp_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup temp file {tmp_path}: {e}")
        
        for pdf_path in pdf_paths:
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.unlink(pdf_path)
                    logger.debug(f"Cleaned up PDF file: {pdf_path}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup PDF file {pdf_path}: {e}")



@router.post("/{exam_id}/generate", response_model=dict)
async def start_exam_generation(
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
):
    """
    Start content generation for a planned exam.
    
    This endpoint triggers the Celery task to generate all topic content
    for an exam that has been planned but not yet generated.
    """
    from app.tasks.exam_tasks import generate_exam_content
    
    # Get exam to verify it exists and belongs to user
    exam = await exam_service.get_exam(current_user.id, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    
    # Verify exam is in planned status
    if exam.status != "planned":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start generation for exam with status '{exam.status}'. Exam must be in 'planned' status."
        )
    
    # Update status to generating
    exam.status = "generating"
    exam.progress = 0.0
    exam.current_step = "Initializing content generation..."
    await exam_service.exam_repo.update(exam)
    await exam_service.exam_repo.session.commit()
    
    # Trigger Celery task
    try:
        generate_exam_content.delay(str(exam.id), str(current_user.id))
        logger.info(f"✅ Started content generation for exam {exam.id}")
        
        return {
            "message": "Content generation started",
            "exam_id": str(exam.id),
            "status": "generating"
        }
    except Exception as e:
        logger.error(f"Failed to start generation task: {e}", exc_info=True)
        # Revert status
        exam.status = "planned"
        exam.progress = None
        exam.current_step = None
        await exam_service.exam_repo.update(exam)
        await exam_service.exam_repo.session.commit()
        
        raise HTTPException(
            status_code=500,
            detail="Failed to start content generation. Please try again."
        )


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
            flashcard_count=t.flashcard_count,
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


@router.get("/{exam_id}/status", response_model=GenerationStatusResponse)
async def get_generation_status(
    exam_id: UUID,
    current_user: User = Depends(get_current_active_user),
    exam_service: ExamService = Depends(get_exam_service),
    db: AsyncSession = Depends(get_db),
):
    """Get generation status"""

    exam = await exam_service.get_exam(current_user.id, exam_id)
    if not exam:
        raise NotFoundException("Exam", str(exam_id))

    topic_repo = TopicRepository(db)
    topics = await topic_repo.get_by_exam_id(exam_id)
    total = len(topics)
    ready = len([t for t in topics if t.status == "ready" and t.content])

    progress = (ready / total) if total else 0.0
    current_step = None
    for t in topics:
        if t.status != "ready":
            current_step = t.topic_name
            break

    return GenerationStatusResponse(
        exam_id=exam_id,
        status=exam.status,
        progress=progress,
        current_step=current_step,
        total_steps=total if total else None,
        completed_steps=ready if total else None,
    )
