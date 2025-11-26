"""
V3.0 Exam creation with integrated plan generation and caching.

This method:
1. Creates exam in 'planning' status
2. Generates plan with CachedCoursePlanner (creates cache + uploads to S3)
3. Stores plan_data and cache info
4. Triggers initial prefetch (first 2 topics)
5. Returns exam with plan ready
"""
from typing import Tuple
from uuid import UUID
from datetime import datetime, timedelta

from app.domain.exam import Exam
from app.domain.user import User
from app.agent.schemas import ExamPlan
from app.agent.cached_planner import CachedCoursePlanner
from app.integrations.storage import SupabaseStorage
from app.integrations.llm.cache_manager import ContextCacheManager
from app.services.generation_service import GenerationService


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
    generation_service: GenerationService
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
        generation_service: Generation service for prefetch
    
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
        original_content=original_content
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
        exam_id=exam.id
    )
    
    # Prepare updates dictionary
    updates = {
        "plan_data": plan.model_dump(),
        "cache_name": cache_name,
        "storage_path": f"exams/{exam.id}/original_content.txt",
        "status": "planned",
        "plan_ready_at": datetime.utcnow(),
        "topic_count": plan.total_topics,
    }
    
    if cache_name:
        updates["cache_expires_at"] = datetime.utcnow() + timedelta(hours=1)
    
    # Update exam using service method
    await exam_service.update_exam(
        user_id=exam.user_id,
        exam_id=exam.id,
        updates=updates
    )
    
    # 4. Trigger initial prefetch
    if cache_name:
        await generation_service.prefetch_initial_topics(
            exam_id=exam.id,
            plan=plan,
            cache_name=cache_name
        )
    
    return exam, plan
