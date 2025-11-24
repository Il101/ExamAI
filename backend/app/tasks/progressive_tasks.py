"""
New Celery tasks for progressive generation.
Add these to app/tasks/exam_tasks.py
"""

@celery_app.task(
    bind=True,
    name="create_exam_plan",
    base=ExamGenerationTask,
    max_retries=3,
    default_retry_delay=60,
)
def create_exam_plan(self, exam_id: str, user_id: str):
    """
    Create topic plan for exam without generating content.
    
    This is Phase 1 of progressive generation:
    1. Run CoursePlanner
    2. Save topics as 'pending'
    3. Mark exam as 'planned'
    """
    try:
        result = asyncio.run(
            _create_exam_plan_async(
                exam_id=UUID(exam_id),
                user_id=UUID(user_id),
            )
        )
        return {"status": "success", "topic_count": result}
    except Exception as e:
        error_category, user_message = _categorize_error(e)
        
        # Mark exam as failed
        asyncio.run(_mark_exam_failed(UUID(exam_id), user_message, error_category))
        
        # Retry for transient errors
        if self.request.retries < self.max_retries and error_category in [
            "api_error",
            "timeout",
        ]:
            raise self.retry(exc=e)
        
        raise


async def _create_exam_plan_async(exam_id: UUID, user_id: UUID) -> int:
    """
    Async implementation of plan creation.
    
    Returns:
        Number of topics created
    """
    async with AsyncSessionLocal() as session:
        # Get repositories
        exam_repo = ExamRepository(session)
        topic_repo = TopicRepository(session)
        user_repo = UserRepository(session)
        
        # Get entities
        exam = await exam_repo.get_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")
        
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        
        # Initialize services
        llm_provider = get_llm_provider()
        cost_guard = CostGuardService(UserRepository(session), LLMUsageLogRepository(session))
        
        # Check budget
        estimated_cost = llm_provider.calculate_cost(5000, 5000)  # Rough estimate for planning
        budget_check = await cost_guard.check_budget(user, estimated_cost)
        if not budget_check["allowed"]:
            raise ValueError("Insufficient budget for plan creation")
        
        # Run planner only
        from app.agent.planner import CoursePlanner
        from app.agent.state import AgentState
        
        state = AgentState(
            exam_id=exam_id,
            subject=exam.subject,
            level=exam.level,
            exam_type=exam.exam_type,
            original_content=exam.original_content,
        )
        
        planner = CoursePlanner(llm_provider)
        plan_steps = await planner.make_plan(state)
        
        # Create topics as 'pending'
        topics = []
        for idx, step in enumerate(plan_steps):
            topic = Topic(
                exam_id=exam_id,
                user_id=user_id,
                topic_name=step.title,
                content="",  # Empty for now
                status="pending",
                order_index=idx,
                generation_priority=step.priority.value,
                difficulty_level=3,  # Default
            )
            topics.append(topic)
        
        # Save topics
        created_topics = await topic_repo.bulk_create(topics)
        
        # Mark exam as planned
        exam.mark_as_planned()
        exam.update_topic_count(len(created_topics))
        await exam_repo.update(exam)
        
        # Log usage
        await cost_guard.log_usage(
            user=user,
            tokens_input=state.total_tokens_used // 2,
            tokens_output=state.total_tokens_used // 2,
            cost_usd=state.total_cost_usd,
            operation_type="plan_creation",
        )
        
        await session.commit()
        
        return len(created_topics)


@celery_app.task(
    bind=True,
    name="generate_topic_content",
    base=ExamGenerationTask,
    max_retries=3,
    default_retry_delay=60,
)
def generate_topic_content(self, topic_id: str, user_id: str):
    """
    Generate content for a single topic.
    
    This is Phase 2 of progressive generation:
    1. Generate topic content
    2. Generate flashcards
    3. Mark topic as 'ready'
    """
    try:
        result = asyncio.run(
            _generate_topic_content_async(
                topic_id=UUID(topic_id),
                user_id=UUID(user_id),
            )
        )
        return {"status": "success", "topic_id": topic_id}
    except Exception as e:
        error_category, user_message = _categorize_error(e)
        
        # Mark topic as failed
        asyncio.run(_mark_topic_failed(UUID(topic_id), user_message))
        
        # Retry for transient errors
        if self.request.retries < self.max_retries and error_category in [
            "api_error",
            "timeout",
        ]:
            raise self.retry(exc=e)
        
        raise


async def _generate_topic_content_async(topic_id: UUID, user_id: UUID):
    """
    Async implementation of topic content generation.
    """
    async with AsyncSessionLocal() as session:
        # Get repositories
        topic_repo = TopicRepository(session)
        exam_repo = ExamRepository(session)
        user_repo = UserRepository(session)
        
        # Get entities
        topic = await topic_repo.get_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        exam = await exam_repo.get_by_id(topic.exam_id)
        user = await user_repo.get_by_id(user_id)
        
        # Initialize services
        llm_provider = get_llm_provider()
        cost_guard = CostGuardService(UserRepository(session), LLMUsageLogRepository(session))
        
        # Generate content using TopicExecutor
        from app.agent.executor import TopicExecutor
        from app.agent.state import AgentState, PlanStep
        from app.domain.priority import Priority
        
        state = AgentState(
            exam_id=exam.id,
            subject=exam.subject,
            level=exam.level,
            exam_type=exam.exam_type,
            original_content=exam.original_content,
        )
        
        # Create plan step for this topic
        plan_step = PlanStep(
            id=topic.order_index + 1,
            title=topic.topic_name,
            description="",
            priority=Priority(topic.generation_priority) if topic.generation_priority in [1,2,3] else Priority.MEDIUM,
            estimated_paragraphs=5,
            dependencies=[],
        )
        
        executor = TopicExecutor(llm_provider)
        step_result = await executor.execute_step(state, plan_step, {})
        
        if not step_result.success:
            raise ValueError(f"Failed to generate topic: {step_result.error_message}")
        
        # Mark topic as ready
        topic.mark_as_ready(step_result.content)
        await topic_repo.update(topic)
        
        # Log usage
        await cost_guard.log_usage(
            user=user,
            tokens_input=state.total_tokens_used // 2,
            tokens_output=state.total_tokens_used // 2,
            cost_usd=state.total_cost_usd,
            operation_type="topic_generation",
        )
        
        await session.commit()


async def _mark_topic_failed(topic_id: UUID, error_message: str):
    """Mark topic as failed"""
    async with AsyncSessionLocal() as session:
        topic_repo = TopicRepository(session)
        topic = await topic_repo.get_by_id(topic_id)
        if topic:
            topic.mark_as_failed(error_message)
            await topic_repo.update(topic)
            await session.commit()
