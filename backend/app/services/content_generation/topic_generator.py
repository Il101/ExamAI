from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from uuid import UUID
import logging

from app.agent.executor import TopicExecutor
from app.services.content_generation.flashcard_generator import FlashcardGenerator
from app.services.cache_fallback import CacheFallbackService
from app.repositories.topic_repository import TopicRepository
from app.repositories.exam_repository import ExamRepository
from app.agent.state import AgentState, PlanStep, Priority
from app.utils.content_cleaner import strip_thinking_tags

logger = logging.getLogger(__name__)


@dataclass
class TopicGenerationResult:
    """Result of topic generation including usage metrics."""
    content: str
    tokens_input: int
    tokens_output: int
    cost_usd: float


class TopicContentGenerator:
    """
    Generates content for a single topic.
    
    This is the ONLY place where topic content is generated.
    Used by:
    - Batch generation (Celery task)
    - Incremental generation (on-demand)
    - Manual regeneration
    
    Guarantees:
    1. Cache is ALWAYS used if available (via CacheFallbackService)
    2. Flashcards are ALWAYS created (unless content < 50 chars)
    3. Cache expiration is handled automatically
    4. Content is cleaned (strip_thinking_tags)
    5. Topic status is updated atomically
    
    Preserves:
    - CachedCoursePlanner integration
    - ContextCacheManager usage
    - CacheFallbackService logic
    - All error handling patterns
    """
    
    def __init__(
        self,
        executor: TopicExecutor,
        flashcard_gen: FlashcardGenerator,
        fallback_service: CacheFallbackService,
        topic_repo: TopicRepository,
        exam_repo: ExamRepository
    ):
        """
        Initialize topic content generator.
        
        Args:
            executor: TopicExecutor for AI generation
            flashcard_gen: FlashcardGenerator for creating flashcards
            fallback_service: CacheFallbackService for cache expiration handling
            topic_repo: Repository for topic CRUD
            exam_repo: Repository for exam CRUD
        """
        self.executor = executor
        self.flashcard_gen = flashcard_gen
        self.fallback = fallback_service
        self.topic_repo = topic_repo
        self.exam_repo = exam_repo
    
    async def generate_topic(
        self,
        topic_id: UUID,
        cache_name: Optional[str] = None,
        exam_id: Optional[UUID] = None,
        output_language: Optional[str] = None,
    ) -> TopicGenerationResult:
        """
        Backward compatible wrapper for a single topic.
        """
        results = await self.generate_batch(
            topic_ids=[topic_id],
            cache_name=cache_name,
            exam_id=exam_id,
            output_language=output_language
        )
        if topic_id not in results:
            raise ValueError(f"Generation failed for topic {topic_id}")
        return results[topic_id]

    async def generate_batch(
        self,
        topic_ids: List[UUID],
        cache_name: Optional[str] = None,
        exam_id: Optional[UUID] = None,
        output_language: Optional[str] = None,
        include_quizzes: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate content, flashcards, and MCQs for a batch of topics.
        
        Returns:
            Dict containing:
            - results: Dict[UUID, TopicGenerationResult]
            - usage: Dict[str, Any] (aggregated tokens/cost)
        """
        if not topic_ids:
            return {"results": {}, "usage": {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}}

        print(f"[PIPELINE] BATCH_START topics={len(topic_ids)}")

        # 1. Fetch topics and exam
        topics = [await self.topic_repo.get_by_id(tid) for tid in topic_ids]
        topics = [t for t in topics if t]
        if not topics:
            return {"results": {}, "usage": {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}}

        if not exam_id:
            exam_id = topics[0].exam_id
        exam = await self.exam_repo.get_by_id(exam_id)
        if not exam:
            raise ValueError(f"Exam {exam_id} not found")

        effective_cache_name = cache_name or exam.cache_name
        lang = output_language or "ru"

        # 2. Build AgentState
        state = AgentState(
            user_request=f"Generate content for {len(topics)} topics",
            subject=exam.subject,
            level=exam.level,
            exam_type=exam.exam_type,
            original_content=exam.original_content or "",
            cache_name=effective_cache_name,
            output_language=lang
        )
        
        # Prepare PlanSteps for the batch
        state.plan = [
            PlanStep(
                id=t.id,
                title=t.topic_name,
                description=f"Generate content for {t.topic_name}",
                priority=Priority.MEDIUM,
                estimated_paragraphs=5
            ) for t in topics
        ]

        logger.info(f"Executing batch generation for {len(topics)} topics")

        # 3. Execute theory with fallback
        async def _execute_batch_op(cn: Optional[str]):
            state.cache_name = cn
            content_map = await self.executor.execute_batch(state, state.plan)
            return content_map

        raw_result, updated_cache_name = await self.fallback.execute_with_fallback(
            exam_id=exam_id,
            cache_name=effective_cache_name,
            operation=_execute_batch_op
        )
        
        # Robust unpacking: execute_with_fallback returns (op_result, new_cache)
        # and op_result is whatever our lambda returns.
        batch_result_map = raw_result
        if isinstance(raw_result, tuple) and len(raw_result) == 2 and isinstance(raw_result[1], bool):
            # Handle legacy/buggy nested tuple if it somehow persists
            batch_result_map = raw_result[0]

        effective_cache_name = updated_cache_name or effective_cache_name

        # 4. Process theory results
        generation_results = {}
        topics_data_for_cards = []
        
        for topic in topics:
            topic_id_str = str(topic.id)
            if topic_id_str in batch_result_map:
                content = batch_result_map[topic_id_str]
                
                # State machine transition
                if topic.status != "generating":
                    if topic.status in ["pending", "failed"] or (topic.status == "ready" and not topic.content):
                        # Force back to generating so we can mark as ready
                        topic.status = "generating"
                    else:
                        logger.warning(f"Skipping topic {topic.id}: reached unexpected status {topic.status}")
                        continue
                
                topic.mark_as_ready(content)
                await self.topic_repo.update(topic)
                print(f"[PIPELINE] topic_saved topic_id={topic.id} content_len={len(content)}")
                
                generation_results[topic.id] = TopicGenerationResult(
                    content=content,
                    tokens_input=0, # usage is in state
                    tokens_output=0,
                    cost_usd=0.0
                )
                
                if len(content) >= self.flashcard_gen.MIN_CONTENT_LENGTH:
                    topics_data_for_cards.append({
                        "id": topic.id,
                        "title": topic.topic_name,
                        "content": content
                    })

        # 5. Generate flashcards AND MCQs in batch
        total_usage = {
            "tokens_input": state.total_tokens_input,
            "tokens_output": state.total_tokens_output,
            "cost_usd": state.total_cost_usd
        }

        if topics_data_for_cards and include_quizzes:
            # Generate Flashcards
            try:
                print(f"[PIPELINE] generating flashcard batch for {len(topics_data_for_cards)} topics")
                cards_map, cards_usage = await self.flashcard_gen.create_for_batch(
                    topics_data=topics_data_for_cards,
                    user_id=topics[0].user_id,
                    cache_name=effective_cache_name
                )
                total_usage["tokens_input"] += cards_usage.get("tokens_input", 0)
                total_usage["tokens_output"] += cards_usage.get("tokens_output", 0)
                total_usage["cost_usd"] += cards_usage.get("cost_usd", 0.0)
            except Exception as e:
                logger.error(f"Flashcard batch generation failed: {e}")

            # Generate MCQs (newly added to batch)
            try:
                print(f"[PIPELINE] generating MCQ batch for {len(topics_data_for_cards)} topics")
                mcq_map, mcq_usage = await self.flashcard_gen.quiz_generator.generate_mcq_batch(
                    topics_data=topics_data_for_cards,
                    num_questions_per_topic=2
                )
                
                # Save MCQs to database (caching them immediately)
                for topic in topics:
                    topic_id_str = str(topic.id)
                    if topic_id_str in mcq_map:
                        questions = mcq_map[topic_id_str]
                        questions_data = []
                        for idx, q in enumerate(questions):
                            # Unify format: convert distractor list to flat dict
                            distractors_dict = {}
                            if hasattr(q.explanation, 'distractors') and isinstance(q.explanation.distractors, list):
                                for dist in q.explanation.distractors:
                                    distractors_dict[dist.option] = dist.text
                            elif hasattr(q.explanation, 'distractors') and isinstance(q.explanation.distractors, dict):
                                distractors_dict = q.explanation.distractors

                            questions_data.append({
                                "id": idx,
                                "question": q.question,
                                "options": [
                                    {"id": opt_idx, "text": opt.text, "is_correct": opt.is_correct}
                                    for opt_idx, opt in enumerate(q.options)
                                ],
                                "explanation": {
                                    "correct": q.explanation.correct,
                                    "distractors": distractors_dict
                                }
                            })
                        
                        topic.quiz_data = {"questions": questions_data}
                        await self.topic_repo.update(topic)
                        print(f"[PIPELINE] mcqs_saved topic_id={topic.id} count={len(questions)}")
                
                total_usage["tokens_input"] += mcq_usage.get("tokens_input", 0)
                total_usage["tokens_output"] += mcq_usage.get("tokens_output", 0)
                total_usage["cost_usd"] += mcq_usage.get("cost_usd", 0.0)
            except Exception as e:
                logger.error(f"MCQ batch generation failed: {e}")

        print(f"[PIPELINE] BATCH_DONE cost=${total_usage['cost_usd']:.4f}")
        return {"results": generation_results, "usage": total_usage}

    async def regenerate_topic(
        self,
        topic_id: UUID,
        force_new_cache: bool = False
    ) -> TopicGenerationResult:
        """
        Regenerate content for an existing topic.
        
        Useful for:
        - User wants to regenerate content
        - Content quality is poor
        - Fixing generation errors
        
        Args:
            topic_id: Topic to regenerate
            force_new_cache: If True, don't use existing cache
            
        Returns:
            Newly generated content and usage metrics
        """
        topic = await self.topic_repo.get_by_id(topic_id)
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")
        
        exam = await self.exam_repo.get_by_id(topic.exam_id)
        
        cache_name = None if force_new_cache else exam.cache_name
        
        logger.info(
            f"Regenerating topic {topic_id}: '{topic.topic_name}' "
            f"(force_new_cache: {force_new_cache})"
        )
        
        return await self.generate_topic(
            topic_id=topic_id,
            cache_name=cache_name,
            exam_id=exam.id
        )
