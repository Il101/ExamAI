import json
import logging
from typing import List, Any, Optional, Dict

from pydantic import BaseModel, Field

from app.integrations.llm.base import LLMProvider
from app.core.config import settings
from google.genai import types
import asyncio
from typing import List, Any, Optional, Dict, Tuple
from app.agent.schemas import ReflectionResult

logger = logging.getLogger(__name__)


class FlashcardSchema(BaseModel):
    id: Optional[Any] = Field(None, description="ID of the topic (from current batch)")
    front: str = Field(..., description="The question or front of the card")
    back: str = Field(..., description="The answer or back of the card")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty level 1-5")
    tags: List[str] = Field(default_factory=list, description="Relevant tags")


class FlashcardBatchSchema(BaseModel):
    """Schema for a batch of flashcards for multiple topics"""
    cards: List[FlashcardSchema] = Field(..., description="List of generated flashcards with topic IDs")


class FlashcardSetSchema(BaseModel):
    """Schema for a set of flashcards (for a single topic)"""
    cards: List[FlashcardSchema] = Field(..., description="List of generated flashcards")


class MCQOption(BaseModel):
    """Single option for a multiple choice question"""
    text: str = Field(..., description="Option text")
    is_correct: bool = Field(..., description="Whether this is the correct answer")


class DistractorExplanation(BaseModel):
    """Explanation for why a distractor is wrong"""
    option: str = Field(..., description="Option letter (A, B, C, or D)")
    text: str = Field(..., description="Explanation of why this option is incorrect")


class MCQExplanation(BaseModel):
    """Deep explanation for MCQ"""
    correct: str = Field(..., description="Why the correct answer is right (2-3 sentences)")
    distractors: List[DistractorExplanation] = Field(..., description="List of explanations for each incorrect option")


class MCQQuestion(BaseModel):
    id: Optional[Any] = Field(None, description="ID of the topic (from current batch)")
    question: str = Field(..., description="The question text")
    options: List[MCQOption] = Field(..., description="List of 4 options")
    correct_answer: str = Field(..., description="The text of the correct option")
    explanation: MCQExplanation = Field(..., description="Explanation of the correct answer")
    difficulty: int = Field(default=3, ge=1, le=5, description="Difficulty 1-5")
    tags: List[str] = Field(default_factory=list, description="Relevant tags")


class MCQQuizSchema(BaseModel):
    """Schema for a single topic MCQ quiz"""
    questions: List[MCQQuestion] = Field(..., description="List of MCQ questions")


class MCQBatchSchema(BaseModel):
    """Schema for a batch of MCQs for multiple topics"""
    questions: List[MCQQuestion] = Field(..., description="List of MCQ questions with topic IDs")


class QuizGenerator:
    """
    Generates study materials (flashcards/quizzes) from content using AI.
    Uses Gemini Structured Output for reliable generation.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_flashcards(
        self, 
        content: str, 
        num_cards: int = 5,
        cache_name: str = None,
        exam_id: "UUID" = None
    ) -> tuple[List[FlashcardSchema], dict[str, Any]]:
        """
        Generate flashcards from the provided content.

        Args:
            content: Study material text
            num_cards: Target number of cards to generate

        Returns:
            Tuple of (List of FlashcardSchema objects, usage_metadata dict)
        """
        
        from app.prompts import load_prompt
        
        logger.info("Generating flashcards", extra={
            "component": "quiz_generator",
            "num_cards": num_cards,
            "has_cache": cache_name is not None,
            "cache_name": cache_name,
            "content_length": len(content) if content else 0
        })
        
        # Use cache if available, otherwise use content directly
        # NOTE: Flashcards are generated from the provided 'content' string (the topic summary).
        # However, we will use the cache for REFLECTION (verification layer).
        
        # Build prompt with full content
        prompt = load_prompt(
            'quiz/flashcards.txt',
            num_cards=num_cards,
            content=content
        )
        
        # Retry mechanism for transient 504 errors (server overload during prefill)
        # First attempt may hit overloaded servable, retry gets routed to different server
        max_retries = 2  # Reduced from 3 (SDK already retries once)
        last_error = None
        current_model = settings.GEMINI_QUIZ_MODEL
        fallback_model = settings.GEMINI_QUIZ_FALLBACK_MODEL
        
        for attempt in range(max_retries):
            try:
                # Generate with AGGRESSIVE timeout (50s) to fail fast on stuck requests
                # Normal generation takes ~15s. If > 50s, it's likely stuck -> retry immediately.
                # Use GeminiProvider.generate for robust retries + counting
                llm_response = await self.llm.generate(
                    prompt=prompt,
                    model=current_model, # Explicitly use quiz model
                    temperature=0.3,
                    system_prompt="You are an expert tutor creating study materials.",
                    response_schema=FlashcardSetSchema, # Use schema for stability
                    # Timeout handled by GeminiProvider (180s) or passing explicit
                    timeout=120.0,
                                        max_tokens=4000  # Increased for individual topic search-notes/explanations
                )
                
                # If response_schema is used, llm_response.parsed is the validated object
                flashcard_set = llm_response.parsed
                
                # --- VERIFICATION LAYER: Reflection ---
                if flashcard_set and flashcard_set.cards and cache_name:
                    try:
                        # Convert cards to text for reflection
                        generated_txt = "\n".join([f"Q: {c.front}\nA: {c.back}" for c in flashcard_set.cards])
                        reflection = await self._reflect_on_quiz(
                            title="Flashcards",
                            generated_content=generated_txt,
                            cache_name=cache_name,
                            source_context=None # Use cache
                        )
                        
                        if not reflection.is_accurate or not reflection.pedagogical_alignment:
                            logger.warning(f"[QuizGen] ⚠️ Quiz Reflection failed, attempting self-correction")
                            
                            # Self-correction attempt
                            prompt_fix = (
                                f"{prompt}\n\n"
                                f"--- \n"
                                f"⚠️ **SELF-CORRECTION REQUIRED** ⚠️\n"
                                f"Previous flashcards had issues:\n"
                                + "\n".join([f"- {e}" for e in reflection.errors + reflection.hallucinations]) +
                                f"\n\n**FIX INSTRUCTIONS:**\n{reflection.suggestions}\n"
                                f"Regenerate the flashcards fixing these issues."
                            )
                            
                            llm_response = await self.llm.generate(
                                prompt=prompt_fix,
                                model=current_model,
                                temperature=0.2,
                                response_schema=FlashcardSetSchema,
                                cache_name=cache_name,
                                timeout=120.0
                            )
                            flashcard_set = llm_response.parsed
                    except Exception as re:
                        logger.error(f"[QuizGen] Reflection error: {re}")
                # --- END VERIFICATION ---
                
                # If parsing failed or wasn't used, fallback to manual parse
                if not flashcard_set:
                    try:
                        data = self._parse_json(llm_response.content)
                        if isinstance(data, dict) and "cards" in data:
                            flashcard_set = FlashcardSetSchema(cards=data["cards"])
                        elif isinstance(data, list):
                            flashcard_set = FlashcardSetSchema(cards=data)
                    except Exception as parse_error:
                        logger.error(f"Manual parse failed for flashcards: {parse_error}")
                
                if not flashcard_set or not flashcard_set.cards:
                    raise ValueError("Failed to get valid flashcards from LLM response")

                flashcards = flashcard_set.cards
                
                usage = {
                    "tokens_input": llm_response.tokens_input,
                    "tokens_output": llm_response.tokens_output,
                    "cost_usd": llm_response.cost_usd,
                }
                
                logger.info("Generated %s flashcards using %s", len(flashcards), current_model, extra={"component": "quiz_generator", "count": len(flashcards)})
                return flashcards, usage
                    
            except (RuntimeError, ValueError) as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check for recoverable errors:
                # 1. API Errors: 503, 504, timeout, overloaded
                # 2. Content Errors: JSON parsing failed (ValueError)
                is_api_error = any(x in error_msg for x in ["504", "deadline_exceeded", "timed out", "503", "overloaded"])
                is_json_error = "json" in error_msg or "delimiter" in error_msg or "parse" in error_msg or "failed to generate" in error_msg

                if (is_api_error or is_json_error) and attempt < max_retries - 1:
                    retry_wait = 2.0 * (attempt + 1)  # Linear backoff for content errors
                    
                    # Switch to fallback model on overload
                    if ("503" in error_msg or "overloaded" in error_msg) and current_model != fallback_model:
                        logger.warning(
                            f"Flashcard generation overload on {current_model}, switching to fallback {fallback_model}",
                            extra={"component": "quiz_generator"}
                        )
                        current_model = fallback_model
                    
                    logger.warning(
                        f"Generation attempt {attempt + 1} failed: {str(e)}. Retrying in {retry_wait}s...",
                        extra={"component": "quiz_generator"}
                    )
                    await asyncio.sleep(retry_wait)
                    continue
                
                # If retries exhausted or non-recoverable error
                logger.error(
                    f"All {max_retries} attempts failed for flashcards. Last error: {str(e)}",
                    extra={"component": "quiz_generator"}
                )
                raise last_error
        
        # All retries exhausted
        raise last_error if last_error else RuntimeError("Unknown error in flashcard generation")

    def _parse_json(self, text: str) -> Any:
        """
        Robustly parse JSON from text, handling markdown blocks and trailing text.
        """
        text = text.strip()
        
        # Strip markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
        elif text.startswith("```"):
            text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
        text = text.strip()
        
        try:
            # Try standard load first
            return json.loads(text)
        except json.JSONDecodeError as e:
            # Check for "Extra data" error (content after valid JSON)
            if "Extra data" in str(e):
                try:
                    # raw_decode returns (obj, end_index)
                    # It parses the first valid JSON object it finds
                    decoder = json.JSONDecoder()
                    obj, _ = decoder.raw_decode(text)
                    return obj
                except Exception:
                    # If raw_decode fails, simple regex fallback
                    pass
            
            # Try finding the largest JSON-like block
            import re
            # Find everything between first { and last } OR first [ and last ]
            # This is a fallback heuristic
            match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except:
                    pass
            
            raise e

    async def generate_flashcards_batch(
        self,
        topics_data: List[Dict[str, Any]],
        num_cards_per_topic: int = 3,
        max_retries: int = 2,
        cache_name: Optional[str] = None
    ) -> tuple[Dict[int, List[FlashcardSchema]], dict[str, Any]]:
        """
        Generate flashcards for multiple topics at once.
        topics_data: [{'id': 1, 'title': 'Topic', 'content': '...'}]
        """
        if not topics_data:
            return {}, {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}

        current_model = settings.GEMINI_QUIZ_MODEL
        topics_summary = "\n".join([f"- {t['id']}: {t['title']}" for t in topics_data])
        contents_block = "\n\n".join([f"--- TOPIC {t['id']}: {t['title']} ---\n{t['content']}" for t in topics_data])

        from app.prompts import load_prompt
        prompt = load_prompt(
            'quiz/flashcards_batch.txt',
            num_cards_per_topic=num_cards_per_topic,
            topics_summary=topics_summary,
            contents_block=contents_block
        )

        for attempt in range(max_retries):
            try:
                llm_response = await self.llm.generate(
                    prompt=prompt,
                    model=current_model,
                    temperature=0.3,
                    system_prompt="You are an expert tutor creating study materials for multiple topics.",
                    response_schema=FlashcardBatchSchema,
                    timeout=120.0,
                    max_tokens=12000, # Increased for batch generation
                    operation_type="flashcard_batch_generation",
                    cache_name=cache_name
                )
                
                batch_result = llm_response.parsed
                if not batch_result:
                    raise ValueError("Failed to parse flashcard batch")

                # Group by topic ID and VERIFY
                grouped_cards = {}
                for card in batch_result.cards:
                    # VERIFICATION LAYER: Check each card in batch
                    is_valid = True
                    if cache_name:
                        try:
                            # Simple text representation of the card
                            card_txt = f"Q: {card.front}\nA: {card.back}"
                            # We can't easily find the full topic text here, 
                            # but we can verify against the full source cache.
                            reflection = await self._reflect_on_quiz(
                                title=f"Flashcard Batch Item (Topic {card.id})",
                                generated_content=card_txt,
                                cache_name=cache_name,
                                source_context=None
                            )
                            if not reflection.is_accurate or not reflection.pedagogical_alignment:
                                logger.warning(f"[QuizGen] Batch card verification failed for topic {card.id}")
                                is_valid = False
                        except Exception as re:
                            logger.error(f"[QuizGen] Batch card reflection error: {re}")
                    
                    if is_valid:
                        if card.id not in grouped_cards:
                            grouped_cards[card.id] = []
                        grouped_cards[card.id].append(card)

                usage = {
                    "tokens_input": llm_response.tokens_input,
                    "tokens_output": llm_response.tokens_output,
                    "cost_usd": llm_response.cost_usd,
                }
                
                return grouped_cards, usage
            except Exception as e:
                logger.warning(f"Flashcard batch attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    raise

    async def generate_mcq_batch(
        self,
        topics_data: List[Dict[str, Any]],
        num_questions_per_topic: int = 2,
        max_retries: int = 2,
        cache_name: Optional[str] = None
    ) -> tuple[Dict[int, List[MCQQuestion]], dict[str, Any]]:
        """
        Generate MCQs for multiple topics at once.
        """
        if not topics_data:
            return {}, {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}

        current_model = settings.GEMINI_QUIZ_MODEL
        topics_summary = "\n".join([f"- {t['id']}: {t['title']}" for t in topics_data])
        contents_block = "\n\n".join([f"--- TOPIC {t['id']}: {t['title']} ---\n{t['content']}" for t in topics_data])

        from app.prompts import load_prompt
        prompt = load_prompt(
            'quiz/mcq_questions_batch.txt',
            num_questions_per_topic=num_questions_per_topic,
            topics_summary=topics_summary,
            contents_block=contents_block
        )

        for attempt in range(max_retries):
            try:
                llm_response = await self.llm.generate(
                    prompt=prompt,
                    model=current_model,
                    temperature=0.4,
                    system_prompt="You are an expert tutor creating educational assessments for multiple topics.",
                    response_schema=MCQBatchSchema,
                    timeout=120.0,
                    max_tokens=15000, # Increased for batch generation with detailed explanations
                    operation_type="mcq_batch_generation",
                    cache_name=cache_name
                )
                
                batch_result = llm_response.parsed
                if not batch_result:
                    raise ValueError("Failed to parse MCQ batch")

                # Group by topic ID and VERIFY
                grouped_questions = {}
                for q in batch_result.questions:
                    # VERIFICATION LAYER: Check each question in batch
                    is_valid = True
                    if cache_name:
                        try:
                            opts = "\n".join([f"- {opt.text} ({'Correct' if opt.is_correct else 'Wrong'})" for opt in q.options])
                            q_txt = f"Q: {q.question}\nOptions:\n{opts}\nExplanation: {q.explanation.correct}"
                            
                            reflection = await self._reflect_on_quiz(
                                title=f"MCQ Batch Item (Topic {q.id})",
                                generated_content=q_txt,
                                cache_name=cache_name,
                                source_context=None
                            )
                            if not reflection.is_accurate or not reflection.pedagogical_alignment:
                                logger.warning(f"[QuizGen] Batch MCQ verification failed for topic {q.id}")
                                is_valid = False
                        except Exception as re:
                            logger.error(f"[QuizGen] Batch MCQ reflection error: {re}")
                    
                    if is_valid:
                        if q.id not in grouped_questions:
                            grouped_questions[q.id] = []
                        grouped_questions[q.id].append(q)

                usage = {
                    "tokens_input": llm_response.tokens_input,
                    "tokens_output": llm_response.tokens_output,
                    "cost_usd": llm_response.cost_usd,
                }
                
                return grouped_questions, usage
            except Exception as e:
                logger.warning(f"MCQ batch attempt {attempt+1} failed: {e}")
                if attempt == max_retries - 1:
                    raise

    async def generate_mcq_quiz(
        self, 
        content: str, 
        num_questions: int = 5,
        cache_name: str = None
    ) -> tuple[List[MCQQuestion], dict[str, Any]]:
        """
        Generate multiple choice questions from the provided content.
        
        Args:
            content: Study material text (from topic content)
            num_questions: Number of questions to generate (1-10)
        
        Returns:
            Tuple of (List of MCQQuestion objects, usage_metadata dict)
        """
        
        from app.prompts import load_prompt
        from google.genai import types
        import time
        import asyncio
        
        start_time = time.time()
        
        logger.info("Generating MCQ questions", extra={
            "component": "quiz_generator",
            "num_questions": num_questions,
            "content_length": len(content) if content else 0
        })
        
        # Retry mechanism for transient errors
        max_retries = 3
        last_error = None
        current_model = settings.GEMINI_QUIZ_MODEL
        fallback_model = settings.GEMINI_QUIZ_FALLBACK_MODEL
        json_text = None
        
        for attempt in range(max_retries):
            try:
                # Load prompt with full content
                prompt = load_prompt(
                    'quiz/mcq_questions.txt',
                    num_questions=num_questions,
                    content=content
                )
                
                # Generate with structured output using the standard wrapper
                llm_response = await self.llm.generate(
                    prompt=prompt,
                    model=current_model,
                    temperature=0.4,
                    system_prompt="You are an expert tutor creating educational assessments.",
                    response_schema=MCQQuizSchema,
                    timeout=60.0,
                    operation_type="mcq_generation",
                    cache_name=cache_name # Use cache for grounding if available
                )
                
                # Get the parsed object
                mcq_quiz = llm_response.parsed
                
                # --- VERIFICATION LAYER: Reflection ---
                if mcq_quiz and mcq_quiz.questions and cache_name:
                    try:
                        # Convert MCQs to text for reflection
                        generated_txt = ""
                        for q in mcq_quiz.questions:
                            opts = "\n".join([f"- {opt.text} ({'Correct' if opt.is_correct else 'Wrong'})" for opt in q.options])
                            generated_txt += f"Q: {q.question}\nOptions:\n{opts}\nExplanation: {q.explanation.correct}\n\n"
                        
                        reflection = await self._reflect_on_quiz(
                            title="MCQ Quiz",
                            generated_content=generated_txt,
                            cache_name=cache_name,
                            source_context=None
                        )
                        
                        if not reflection.is_accurate or not reflection.pedagogical_alignment:
                            logger.warning(f"[QuizGen] ⚠️ MCQ Reflection failed, attempting self-correction")
                            
                            prompt_fix = (
                                f"{prompt}\n\n"
                                f"--- \n"
                                f"⚠️ **SELF-CORRECTION REQUIRED** ⚠️\n"
                                f"Previous MCQs had issues:\n"
                                + "\n".join([f"- {e}" for e in reflection.errors + reflection.hallucinations]) +
                                f"\n\n**FIX INSTRUCTIONS:**\n{reflection.suggestions}\n"
                                f"Regenerate fixing these issues."
                            )
                            
                            llm_response = await self.llm.generate(
                                prompt=prompt_fix,
                                model=current_model,
                                temperature=0.2,
                                response_schema=MCQQuizSchema,
                                cache_name=cache_name,
                                timeout=120.0
                            )
                            mcq_quiz = llm_response.parsed
                    except Exception as re:
                        logger.error(f"[QuizGen] MCQ Reflection error: {re}")
                # --- END VERIFICATION ---
                
                # Fallback to manual parse if needed
                if not mcq_quiz:
                    try:
                        data = self._parse_json(llm_response.content)
                        if isinstance(data, dict) and "questions" in data:
                            mcq_quiz = MCQQuizSchema(questions=data["questions"])
                        elif isinstance(data, list):
                            mcq_quiz = MCQQuizSchema(questions=data)
                    except Exception as e:
                        logger.error(f"Manual MCQ parse failed: {e}")

                if not mcq_quiz or not mcq_quiz.questions:
                    raise ValueError("Failed to get valid MCQ questions from LLM")

                questions = mcq_quiz.questions
                usage = {
                    "tokens_input": llm_response.tokens_input,
                    "tokens_output": llm_response.tokens_output,
                    "cost_usd": llm_response.cost_usd,
                }
                
                duration = time.time() - start_time
                logger.info(
                    f"Successfully generated {len(questions)} MCQ questions with {current_model} in {duration:.2f}s",
                    extra={
                        "component": "quiz_generator",
                        "duration_seconds": round(duration, 2),
                        "questions_count": len(questions)
                    }
                )
                
                return questions, usage
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check for retryable conditions
                is_retryable = (
                    "504" in error_msg or 
                    "deadline_exceeded" in error_msg or 
                    "timed out" in error_msg or
                    "overloaded" in error_msg or
                    "resource exhausted" in error_msg or
                    "429" in error_msg
                )

                if is_retryable and attempt < max_retries - 1:
                    # Switch to fallback model on overload
                    if ("503" in error_msg or "overloaded" in error_msg) and current_model != fallback_model:
                        logger.warning(
                            f"MCQ generation overload on {current_model}, switching to fallback {fallback_model}",
                            extra={"component": "quiz_generator"}
                        )
                        current_model = fallback_model

                    wait_time = 2 * (2 ** attempt)
                    logger.warning(
                        "MCQ generation issue (%s), retry %s/%s in %ss",
                        "TIMEOUT/OVERLOAD",
                        attempt + 1, max_retries, wait_time,
                        extra={
                            "component": "quiz_generator", 
                            "attempt": attempt + 1, 
                            "wait_time": wait_time, 
                            "model": current_model
                        }
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Last attempt or non-retryable error
                    if attempt == max_retries - 1:
                        raise last_error
        
        # If loop finishes without returning, it means all retries failed
        raise last_error if last_error else RuntimeError("Failed to generate MCQ quiz after all retries")

    async def _reflect_on_quiz(
        self,
        title: str,
        generated_content: str,
        cache_name: str = None,
        source_context: str = None
    ) -> ReflectionResult:
        """
        Verify quiz content against source material using the Reflector Agent.
        """
        from app.prompts import load_prompt
        
        reflection_prompt = load_prompt(
            'executor/reflection_quiz.txt',
            title=title,
            generated_content=generated_content,
            source_context=source_context or "Refer to cached documents."
        )

        response = await self.llm.generate(
            prompt=reflection_prompt,
            temperature=0.1,  # Low temperature for strict fact-checking
            max_tokens=2000,
            system_prompt="You are a strict fact-checker and pedagogical reviewer.",
            response_schema=ReflectionResult,
            cache_name=cache_name
        )
        
        if response.parsed:
            return response.parsed
        
        # Fallback if parsing fails
        return ReflectionResult(
            is_accurate=True, 
            pedagogical_alignment=True,
            suggestions="No reflections available."
        )
