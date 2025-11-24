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

        try:
            # Run agent
            state = await self.agent.run(
                user_request=f"Create study notes for {exam.title}",
                subject=exam.subject,
                exam_type=exam.exam_type,
                level=exam.level,
                original_content=exam.original_content,
                progress_callback=progress_callback,
            )

            # Save results
            # We split total tokens roughly 50/50 for input/output if not tracked separately per step
            # But AgentState tracks total tokens used.
            # We don't have exact breakdown of input/output in AgentState total,
            # but we can approximate or improve AgentState to track them separately.
            # For now, we'll use the approximation from the doc.

            exam.mark_as_ready(
                ai_summary=state.final_notes,
                token_input=state.total_tokens_used // 2,  # Approximate
                token_output=state.total_tokens_used // 2,
                cost=state.total_cost_usd,
            )

            # Save topics and generate quizzes
            for i, plan_step in enumerate(state.plan):
                result = state.results.get(plan_step.id)
                content = result.content if result and result.success else ""

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
