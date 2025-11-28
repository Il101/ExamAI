from typing import Awaitable, Callable, Optional
from uuid import UUID

from app.agent.orchestrator import PlanAndExecuteAgent
from app.agent.quiz_generator import QuizGenerator
from app.domain.exam import Exam
from app.domain.review import ReviewItem
from app.domain.topic import Topic
from app.domain.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.topic_repository import TopicRepository
from app.services.cost_guard_service import CostGuardService
from app.utils.content_cleaner import strip_thinking_tags


class AgentService:
    """
    Service layer for AI agent integration.
    Connects agent to database and business logic.
    """

    def __init__(
        self,
        agent: PlanAndExecuteAgent,
        exam_repo: ExamRepository,
        topic_repo: TopicRepository,
        review_repo: ReviewItemRepository,
        cost_guard: CostGuardService,
    ):
        self.agent = agent
        self.exam_repo = exam_repo
        self.topic_repo = topic_repo
        self.review_repo = review_repo
        self.cost_guard = cost_guard
        self.quiz_generator = QuizGenerator(agent.llm)

    async def generate_exam_content(
        self,
        user: User,
        exam_id: UUID,
        progress_callback: Optional[Callable[[str, float], Awaitable[None]]] = None,
    ) -> Exam:
        """
        Generate exam content using AI agent.

        Args:
            user: User requesting generation
            exam_id: Exam ID to generate content for
            progress_callback: Optional callback for progress updates

        Returns:
            Updated exam with generated content
        """

        # Get exam
        exam = await self.exam_repo.get_by_user_and_id(user.id, exam_id)
        if not exam:
            raise ValueError("Exam not found")

        if exam.status != "generating" and not exam.can_generate():
            raise ValueError(f"Cannot generate exam with status: {exam.status}")

        # Estimate cost
        # Simple estimation: input tokens + 3x output tokens
        # We assume 1 char ~= 0.25 tokens
        estimated_tokens = len(exam.original_content) // 4
        estimated_cost = self.agent.llm.calculate_cost(
            estimated_tokens, estimated_tokens * 3  # Assume 3x output
        )

        # Check budget
        budget_check = await self.cost_guard.check_budget(user, estimated_cost)
        if not budget_check["allowed"]:
            raise ValueError(
                f"Insufficient budget: {budget_check.get('reason', 'Unknown reason')}"
            )

        # Mark as generating
        if exam.status != "generating":
            exam.start_generation()
            await self.exam_repo.update(exam)

        # Check for existing topics (Progressive Generation)
        existing_topics = await self.topic_repo.get_by_exam_id(exam.id)
        existing_plan = None
        
        if existing_topics:
            from app.agent.state import PlanStep, Priority
            existing_plan = []
            for topic in existing_topics:
                existing_plan.append(
                    PlanStep(
                        id=topic.order_index + 1, # PlanStep IDs are usually 1-based
                        title=topic.topic_name,
                        description=f"Generate content for {topic.topic_name}", # Description might be lost, reconstruct generic one
                        priority=Priority(topic.difficulty_level) if topic.difficulty_level in [1,2,3] else Priority.MEDIUM,
                        estimated_paragraphs=5
                    )
                )

        try:
            # Run agent
            state = await self.agent.run(
                user_request=f"Create study notes for {exam.title}",
                subject=exam.subject,
                exam_type=exam.exam_type,
                level=exam.level,
                original_content=exam.original_content,
                existing_plan=existing_plan,
                progress_callback=progress_callback,
            )

            # Save results
            # We split total tokens roughly 50/50 for input/output if not tracked separately per step
            # But AgentState tracks total tokens used.
            # We don't have exact breakdown of input/output in AgentState total,
            # but we can approximate or improve AgentState to track them separately.
            # For now, we'll use the approximation from the doc.

            # Mark as ready with usage stats
            # Note: AgentState tracks total tokens but not input/output separately
            # We approximate 50/50 split - could be improved by tracking separately
            exam.mark_as_ready(
                ai_summary=state.final_notes,
                token_input=state.total_tokens_used // 2,
                token_output=state.total_tokens_used // 2,
                cost=state.total_cost_usd,
            )

            # Save topics and generate quizzes
            # If we used an existing plan, we should UPDATE existing topics, not create new ones.
            # Or if the agent re-created the plan (if existing_plan was None), we create new ones.
            
            for i, plan_step in enumerate(state.plan):
                result = state.results.get(plan_step.id)
                raw_content = result.content if result and result.success else ""
                
                # Clean content (remove <thinking> tags from Executor)
                content = strip_thinking_tags(raw_content)
                
                if existing_plan:
                    # Update existing topic
                    # We assume order is preserved
                    if i < len(existing_topics):
                        topic = existing_topics[i]
                        topic.content = content
                        topic.status = "ready" if result and result.success else "failed"
                        await self.topic_repo.update(topic)
                        created_topic = topic
                    else:
                        # Fallback if plan somehow grew (shouldn't happen with existing_plan)
                        continue
                else:
                    # Create new topic (Old flow or if no plan existed)
                    topic = Topic(
                        exam_id=exam.id,
                        user_id=user.id,
                        topic_name=plan_step.title,
                        content=content,
                        order_index=i,
                        difficulty_level=plan_step.priority.value,
                    )
                    topic.estimate_study_time()
                    created_topic = await self.topic_repo.create(topic)
                
                # Generate Flashcards for this topic
                # Only if content is meaningful
                if content and len(content) > 100:
                    try:
                        if progress_callback:
                            await progress_callback(f"Generating flashcards for {plan_step.title}...", 0.9)
                            
                        flashcards = await self.quiz_generator.generate_flashcards(content, num_cards=3)
                        
                        for card in flashcards:
                            review_item = ReviewItem(
                                topic_id=created_topic.id,
                                user_id=user.id,
                                question=card.front,
                                answer=card.back
                            )
                            await self.review_repo.create(review_item)
                            
                    except Exception as e:
                        print(f"Failed to generate flashcards for topic {plan_step.title}: {e}")
                        # Don't fail the whole exam generation if quiz fails

            exam.update_topic_count(len(state.plan))

            # Log usage
            await self.cost_guard.log_usage(
                user_id=user.id,
                model_name=self.agent.llm.get_model_name(),
                provider="gemini",  # Assuming Gemini for now, or get from LLMProvider
                operation_type="exam_generation",
                input_tokens=state.total_tokens_used // 2,
                output_tokens=state.total_tokens_used // 2,
                cost_usd=state.total_cost_usd,
            )

            # Update exam
            updated = await self.exam_repo.update(exam)

            return updated

        except Exception:
            # Mark as failed
            exam.mark_as_failed()
            await self.exam_repo.update(exam)
            raise

    async def get_status(self, user_id: UUID, exam_id: UUID) -> Optional[dict]:
        """
        Get detailed generation status.
        Calculates progress based on completed topics.
        """
        exam = await self.exam_repo.get_by_user_and_id(user_id, exam_id)
        if not exam:
            return None

        if exam.status == "ready":
            return {
                "exam_id": str(exam_id),
                "status": "ready",
                "progress": 1.0,
                "message": "Generation complete",
                "current_step": "Finalized",
                "steps_completed": exam.topic_count,
                "total_steps": exam.topic_count,
            }
            
        if exam.status == "failed":
             return {
                "exam_id": str(exam_id),
                "status": "failed",
                "progress": 0.0,
                "message": getattr(exam, "error_message", "Generation failed"),
                "current_step": "Failed",
                "steps_completed": 0,
                "total_steps": exam.topic_count,
            }

        # For generating/planned status, calculate from topics
        topics = await self.topic_repo.get_by_exam_id(exam_id)
        if not topics:
             return {
                "exam_id": str(exam_id),
                "status": exam.status,
                "progress": 0.0,
                "message": "Initializing...",
                "current_step": "Planning",
                "steps_completed": 0,
                "total_steps": 0,
            }
            
        total_topics = len(topics)
        completed_topics = len([t for t in topics if t.content and len(t.content) > 0])
        
        # Find current topic
        current_topic_name = "Processing..."
        for t in topics:
            if not t.content or len(t.content) == 0:
                current_topic_name = f"Generating: {t.topic_name}"
                break
        
        progress = completed_topics / total_topics if total_topics > 0 else 0.0
        
        # Adjust progress to be between 0.2 and 0.9 during generation (0.2 is plan created)
        # If status is planned, progress is 0.2
        # If generating, map 0..1 topic completion to 0.2..0.9
        
        if exam.status == "planned":
             return {
                "exam_id": str(exam_id),
                "status": "planned",
                "progress": 0.2,
                "message": "Ready to generate",
                "current_step": "Plan created",
                "steps_completed": 0,
                "total_steps": total_topics,
            }
            
        # Generating
        display_progress = 0.2 + (progress * 0.7)
        
        return {
            "exam_id": str(exam_id),
            "status": "generating",
            "progress": display_progress,
            "message": current_topic_name,
            "current_step": current_topic_name,
            "steps_completed": completed_topics,
            "total_steps": total_topics,
        }
