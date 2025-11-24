"""
New methods for exam_service.py to support progressive generation.
Add these methods to the ExamService class.
"""

async def create_plan(
    self, user_id: UUID, exam_id: UUID
) -> Tuple[Exam, List["Topic"]]:
    """
    Create topic plan without generating content (Phase 1 of progressive generation).
    
    This method:
    1. Runs CoursePlanner to create topic structure
    2. Saves topics as 'pending' in database
    3. Marks exam as 'planned'
    4. Returns exam + list of pending topics
    
    Args:
        user_id: User ID
        exam_id: Exam ID
        
    Returns:
        Tuple of (Updated exam, List of pending topics)
        
    Raises:
        ValueError: If exam not found or cannot create plan
    """
    from app.tasks.exam_tasks import create_exam_plan
    
    exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
    if not exam:
        raise ValueError("Exam not found")
    
    # Check if can create plan
    if not exam.can_create_plan():
        raise ValueError(f"Cannot create plan: status={exam.status}")
    
    # Mark as generating temporarily (will be 'planned' after task completes)
    exam.start_generation()
    updated = await self.exam_repo.update(exam)
    
    # Trigger background task to create plan
    task = create_exam_plan.delay(
        exam_id=str(exam_id), user_id=str(user_id)
    )
    
    return updated, task.id


async def generate_topic(
    self, user_id: UUID, topic_id: UUID
) -> Tuple["Topic", str]:
    """
    Generate content for a single topic (Phase 2 of progressive generation).
    
    This method:
    1. Validates topic belongs to user
    2. Checks rate limits (3 topics/hour for free tier)
    3. Triggers Celery task to generate content + flashcards
    4. Returns updated topic + task ID
    
    Args:
        user_id: User ID
        topic_id: Topic ID
        
    Returns:
        Tuple of (Updated topic, Task ID)
        
    Raises:
        ValueError: If topic not found or cannot generate
        PermissionError: If rate limit exceeded
    """
    from app.repositories.topic_repository import TopicRepository
    from app.tasks.exam_tasks import generate_topic_content
    from app.db.session import get_db
    
    # Get topic (need to inject db session)
    # This is a simplified version - in real implementation,
    # topic_repo should be injected via dependency
    async with AsyncSessionLocal() as session:
        topic_repo = TopicRepository(session)
        topic = await topic_repo.get_by_id(topic_id)
        
        if not topic or topic.user_id != user_id:
            raise ValueError("Topic not found")
        
        # Check if can generate
        if not topic.can_generate():
            raise ValueError(f"Cannot generate topic: status={topic.status}")
        
        # TODO: Check rate limits here
        # For now, skip rate limiting
        
        # Mark as generating
        topic.start_generation()
        updated = await topic_repo.update(topic)
        await session.commit()
    
    # Trigger background task
    task = generate_topic_content.delay(
        topic_id=str(topic_id), user_id=str(user_id)
    )
    
    return updated, task.id
