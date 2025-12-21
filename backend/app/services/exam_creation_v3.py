"""
V3.0 Exam creation with integrated plan generation and caching.

This method:
1. Creates exam in 'planning' status
2. Generates plan with CachedCoursePlanner (creates cache + uploads to S3)
3. Creates Topic records in database from plan
4. Stores plan_data and cache info
5. Triggers initial prefetch (first 2 topics)
6. Returns exam with plan ready
"""
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Tuple
from uuid import UUID
import logging

from app.domain.exam import Exam
from app.domain.user import User
from app.domain.topic import Topic
from app.agent.schemas import ExamPlan
from app.agent.cached_planner import CachedCoursePlanner
from app.integrations.storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager
from app.repositories.topic_repository import TopicRepository

logger = logging.getLogger(__name__)


async def create_exam_with_plan(
    exam_service: "ExamService",
    user: User,
    title: str,
    subject: str,
    exam_type: str,
    level: str,
    original_content: str,
    planner: CachedCoursePlanner,
    storage: SupabaseStorage,
    cache_manager: ContextCacheManager,
    original_file_url: str = None,
    original_file_mime_type: str = None,
    gemini_file_uri: str = None,  # URI for direct Gemini caching (optional)
    original_files: list[dict] | None = None,
    gemini_files: list[dict] | None = None,
    exam_date: datetime | None = None,
) -> Tuple[Exam, ExamPlan]:
    """
    Create exam with automatic plan generation and caching (v3.0)
    
    Args:
        exam_service: ExamService instance
        user: User creating exam
        title: Exam title
        subject: Subject name
        exam_type: Type (oral, written, test)
        level: Level (school, bachelor, master, phd)
        original_content: Study material content
        planner: CachedCoursePlanner instance
        storage: Storage service
        cache_manager: Cache manager
        original_file_url: URL of the original file in storage
        original_file_mime_type: MIME type of the original file
        gemini_file_uri: URI of file in Gemini Files API
    
    Returns:
        Tuple of (Exam, ExamPlan)
    """
    # 1. Create exam in 'planning' status
    exam = await exam_service.create_exam(
        user=user,
        title=title,
        subject=subject,
        exam_type=exam_type,
        level=level,
        original_content=original_content,
        exam_date=exam_date
    )
    
    # 2. Generate plan with cache
    from app.agent.state import AgentState
    
    state = AgentState(
        user_request=f"Create study plan for {subject}",
        subject=subject,
        exam_type=exam_type,
        level=level,
        original_content=original_content
    )
    
    plan, cache_name = await planner.make_plan_with_cache(
        state=state,
        cache_manager=cache_manager,
        storage=storage,
        exam_id=exam.id,
        file_uri=gemini_file_uri,
        mime_type=original_file_mime_type or "application/pdf",
        file_inputs=gemini_files,
    )
    
    # 3. Create Topic records from plan
    # Use the same session as exam_service to ensure transactional consistency
    topic_repo = TopicRepository(exam_service.exam_repo.session)
    
    all_topics = plan.get_all_topics()
    created_topics = []
    
    for idx, topic_plan in enumerate(all_topics):
        topic = Topic(
            exam_id=exam.id,
            user_id=user.id,
            topic_name=topic_plan.title,
            content="",  # Will be generated later
            status="pending",
            order_index=idx,
            generation_priority=1,  # All topics have equal priority for now
            difficulty_level=topic_plan.difficulty_level,
            estimated_study_minutes=topic_plan.estimated_study_minutes,
        )
        created_topic = await topic_repo.create(topic)
        created_topics.append(created_topic)
    
    logger.info(f"Created {len(created_topics)} Topic records for exam {exam.id}")
    
    # 4. Prepare updates dictionary
    primary_file = None
    if original_files:
        primary_file = next((f for f in original_files if f.get("storage_path")), None)

    updates = {
        "plan_data": plan.model_dump(),
        "cache_name": cache_name,
        "storage_path": f"exams/{exam.id}/original_content.txt",
        "status": "planned",
        "plan_ready_at": datetime.now(timezone.utc),
        "topic_count": plan.total_topics,
        "original_file_url": (primary_file or {}).get("storage_path", original_file_url),
        "original_file_mime_type": (primary_file or {}).get("mime_type", original_file_mime_type),
    }
    
    if cache_name:
        updates["cache_expires_at"] = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Update exam using service method
    await exam_service.update_exam(
        user_id=exam.user_id,
        exam_id=exam.id,
        updates=updates
    )
    
    # 5. Fix "TBD" issue: trigger initial scheduling if exam_date is set
    if exam_date:
        try:
            await exam_service.reschedule_exam_topics(user.id, exam.id)
        except Exception as e:
            logger.error(f"Failed to set initial schedule for topics: {e}")
            
    return exam, plan
