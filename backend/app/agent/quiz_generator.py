import json
import logging
from typing import List, Any

from pydantic import BaseModel, Field

from app.integrations.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class FlashcardSchema(BaseModel):
    """Schema for a single flashcard"""
    front: str = Field(..., description="Question or concept on the front of the card")
    back: str = Field(..., description="Answer or explanation on the back of the card")


class FlashcardSetSchema(BaseModel):
    """Schema for a set of flashcards"""
    cards: List[FlashcardSchema] = Field(..., description="List of generated flashcards")


class MCQOption(BaseModel):
    """Single option for a multiple choice question"""
    text: str = Field(..., description="Option text")
    is_correct: bool = Field(..., description="Whether this is the correct answer")


class MCQQuestion(BaseModel):
    """Multiple choice question schema"""
    question: str = Field(..., description="The question text")
    options: List[MCQOption] = Field(..., description="List of 4 options")
    explanation: str = Field(..., description="Explanation of the correct answer")


class MCQQuizSchema(BaseModel):
    """Schema for a set of MCQ questions"""
    questions: List[MCQQuestion] = Field(..., description="List of MCQ questions")


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
    ) -> List[FlashcardSchema]:
        """
        Generate flashcards from the provided content.

        Args:
            content: Study material text
            num_cards: Target number of cards to generate

        Returns:
            List of FlashcardSchema objects
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
        if cache_name:
            try:
                logger.debug("Using context cache for flashcard generation", extra={
                    "component": "quiz_generator",
                    "cache_name": cache_name
                })
                
                # Use cache - remove content placeholder from prompt
                import re
                prompt_template = load_prompt('quiz/flashcards.txt', num_cards=num_cards, content="")
                # Remove the content section since it's in cache
                prompt = re.sub(
                    r'## Source Content\s+\{content\}\s+---',
                    '**IMPORTANT:** The source content is already loaded in the context cache. Analyze it to create flashcards.\n\n---',
                    prompt_template,
                    flags=re.DOTALL
                )
                
                # Call with cache
                from app.core.config import settings
                import asyncio
                logger.debug("Calling Gemini API with cache", extra={
                    "component": "quiz_generator",
                    "model": settings.GEMINI_MODEL,
                    "cache_name": cache_name
                })
                
                # Wrap in timeout (120s like topic content generation)
                response = await asyncio.wait_for(
                    self.llm.client.aio.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        config={
                            "cached_content": cache_name,
                        },
                        contents=[{"role": "user", "parts": [{"text": prompt}]}]
                    ),
                    timeout=120.0
                )
                
                logger.debug("Received response from Gemini API", extra={
                    "component": "quiz_generator",
                    "response_length": len(response.text) if response.text else 0
                })
                
                json_text = response.text
            
            except Exception as cache_error:
                # Check if cache expired
                error_str = str(cache_error).lower()
                if "cache" in error_str and ("not found" in error_str or "expired" in error_str or "404" in error_str):
                    logger.warning("Cache expired, attempting to recreate", extra={"component": "quiz_generator"})
                    
                    # Try to recreate cache if we have exam_id and content
                    if exam_id and content:
                        try:
                            from app.integrations.llm.cache_manager import ContextCacheManager
                            
                            cache_manager = ContextCacheManager(self.llm)
                            logger.info("Recreating cache for exam", extra={"component": "quiz_generator", "exam_id": str(exam_id)})
                            
                            new_cache_name = await cache_manager.create_cache(
                                exam_id=exam_id,
                                content=content,
                                ttl_seconds=3600
                            )
                            logger.info("Successfully recreated cache", extra={"component": "quiz_generator", "cache_name": new_cache_name})
                            
                            # Retry with new cache
                            prompt_template = load_prompt('quiz/flashcards.txt', num_cards=num_cards, content="")
                            prompt = re.sub(
                                r'## Source Content\s+\{content\}\s+---',
                                '**IMPORTANT:** The source content is already loaded in the context cache. Analyze it to create flashcards.\n\n---',
                                prompt_template,
                                flags=re.DOTALL
                            )
                            
                            # Wrap in timeout
                            response = await asyncio.wait_for(
                                self.llm.client.aio.models.generate_content(
                                    model=settings.GEMINI_MODEL,
                                    config={
                                        "cached_content": new_cache_name,
                                    },
                                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                                ),
                                timeout=120.0
                            )
                            
                            json_text = response.text
                            
                        except Exception as recreate_error:
                            logger.error("Failed to recreate cache", extra={"component": "quiz_generator", "error": str(recreate_error)})
                            # Final fallback: use full content
                            logger.warning("Falling back to full content", extra={"component": "quiz_generator"})
                            prompt = load_prompt(
                                'quiz/flashcards.txt',
                                num_cards=num_cards,
                                content=content
                            )
                            
                            response = await self.llm.generate(
                                prompt=prompt,
                                temperature=0.3,
                                system_prompt="You are an expert tutor creating study materials.",
                                response_schema=FlashcardSetSchema,
                                timeout=60.0
                            )
                            
                            json_text = response.content
                    else:
                        # No exam_id - can't recreate cache, use full content
                        logger.warning("No exam_id, falling back to full content", extra={"component": "quiz_generator"})
                        prompt = load_prompt(
                            'quiz/flashcards.txt',
                            num_cards=num_cards,
                            content=content
                        )
                        
                        response = await self.llm.generate(
                            prompt=prompt,
                            temperature=0.3,
                            system_prompt="You are an expert tutor creating study materials.",
                            response_schema=FlashcardSetSchema,
                            timeout=60.0
                        )
                        
                        json_text = response.content
                else:
                    # Not a cache error, re-raise
                    raise
        else:
            # No cache - use full content (no truncation)
            prompt = load_prompt(
                'quiz/flashcards.txt',
                num_cards=num_cards,
                content=content  # Full content, no [:10000] truncation
            )
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                system_prompt="You are an expert tutor creating study materials.",
                response_schema=FlashcardSetSchema,
                timeout=60.0
            )
            
            json_text = response.content

        # Parse response
        try:
            data = self._parse_json(json_text)
            
            # Handle wrapped response
            if isinstance(data, dict) and "cards" in data:
                cards_data = data["cards"]
            elif isinstance(data, list):
                cards_data = data
            else:
                raise ValueError("Invalid response format: expected list or dict with 'cards'")

            # Validate and convert
            flashcards = [FlashcardSchema(**item) for item in cards_data]
            
            logger.info("Generated %s %s", len(flashcards), "flashcards", extra={"component": "quiz_generator", "count": len(flashcards)})
            return flashcards

        except Exception as e:
            logger.error("Error parsing %s", "flashcards", extra={"component": "quiz_generator", "error": str(e)})
            logger.debug("Raw text preview", extra={"component": "quiz_generator", "preview": json_text[:500]})
            raise ValueError(f"Failed to generate flashcards: {str(e)}")

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

    async def generate_mcq_quiz(
        self, 
        content: str, 
        num_questions: int = 5,
        cache_name: str = None,
        exam_id: "UUID" = None
    ) -> List[MCQQuestion]:
        """
        Generate multiple choice questions from the provided content.

        Args:
            content: Study material text
            num_questions: Number of questions to generate

        Returns:
            List of MCQQuestion objects
        """
        
        from app.prompts import load_prompt
        import time
        
        start_time = time.time()
        
        logger.info("Generating MCQ questions", extra={
            "component": "quiz_generator",
            "num_questions": num_questions,
            "has_cache": cache_name is not None,
            "cache_name": cache_name,
            "content_length": len(content) if content else 0
        })
        
        # Use cache if available, otherwise use content directly
        if cache_name:
            try:
                logger.debug("Using context cache for MCQ generation", extra={
                    "component": "quiz_generator",
                    "cache_name": cache_name
                })
                
                # Use cache - remove content placeholder from prompt
                import re
                prompt_template = load_prompt('quiz/mcq_questions.txt', num_questions=num_questions, content="")
                # Remove the content section since it's in cache
                prompt = re.sub(
                    r'## Source Content\s+\{content\}\s+---',
                    '**IMPORTANT:** The source content is already loaded in the context cache. Analyze it to create questions.\n\n---',
                    prompt_template,
                    flags=re.DOTALL
                )
                
                # Call with cache
                from app.core.config import settings
                
                logger.debug("Calling Gemini API with cache for MCQ", extra={
                    "component": "quiz_generator",
                    "model": settings.GEMINI_MODEL,
                    "cache_name": cache_name,
                    "num_questions": num_questions
                })
                
                api_start = time.time()
                response = await self.llm.client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    config={
                        "cached_content": cache_name,
                    },
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                )
                api_duration = (time.time() - api_start) * 1000
                
                logger.info("Received MCQ response from Gemini API", extra={
                    "component": "quiz_generator",
                    "api_duration_ms": round(api_duration, 2),
                    "response_length": len(response.text) if response.text else 0
                })
                
                json_text = response.text
            
            except Exception as cache_error:
                # Check if cache expired
                error_str = str(cache_error).lower()
                if "cache" in error_str and ("not found" in error_str or "expired" in error_str or "404" in error_str):
                    logger.warning("Cache expired, attempting to recreate", extra={"component": "quiz_generator"})
                    
                    # Try to recreate cache if we have exam_id and content
                    if exam_id and content:
                        try:
                            from app.integrations.llm.cache_manager import ContextCacheManager
                            
                            cache_manager = ContextCacheManager(self.llm)
                            logger.info("Recreating cache for exam", extra={"component": "quiz_generator", "exam_id": str(exam_id)})
                            
                            new_cache_name = await cache_manager.create_cache(
                                exam_id=exam_id,
                                content=content,
                                ttl_seconds=3600
                            )
                            logger.info("Successfully recreated cache", extra={"component": "quiz_generator", "cache_name": new_cache_name})
                            
                            # Retry with new cache
                            prompt_template = load_prompt('quiz/mcq_questions.txt', num_questions=num_questions, content="")
                            prompt = re.sub(
                                r'## Source Content\s+\{content\}\s+---',
                                '**IMPORTANT:** The source content is already loaded in the context cache. Analyze it to create questions.\n\n---',
                                prompt_template,
                                flags=re.DOTALL
                            )
                            
                            response = await self.llm.client.aio.models.generate_content(
                                model=settings.GEMINI_MODEL,
                                config={
                                    "cached_content": new_cache_name,
                                },
                                contents=[{"role": "user", "parts": [{"text": prompt}]}]
                            )
                            
                            json_text = response.text
                            
                        except Exception as recreate_error:
                            logger.error("Failed to recreate cache", extra={"component": "quiz_generator", "error": str(recreate_error)})
                            # Final fallback: use full content
                            logger.warning("Falling back to full content", extra={"component": "quiz_generator"})
                            prompt = load_prompt(
                                'quiz/mcq_questions.txt',
                                num_questions=num_questions,
                                content=content
                            )
                            
                            response = await self.llm.generate(
                                prompt=prompt,
                                temperature=0.4,
                                system_prompt="You are an expert tutor creating educational assessments.",
                                response_schema=MCQQuizSchema,
                                timeout=60.0
                            )
                            
                            json_text = response.content
                    else:
                        # No exam_id - can't recreate cache, use full content
                        logger.warning("No exam_id, falling back to full content", extra={"component": "quiz_generator"})
                        prompt = load_prompt(
                            'quiz/mcq_questions.txt',
                            num_questions=num_questions,
                            content=content
                        )
                        
                        response = await self.llm.generate(
                            prompt=prompt,
                            temperature=0.4,
                            system_prompt="You are an expert tutor creating educational assessments.",
                            response_schema=MCQQuizSchema,
                            timeout=60.0
                        )
                        
                        json_text = response.content
                else:
                    # Not a cache error, re-raise
                    raise
        else:
            # No cache - use full content (no truncation)
            prompt = load_prompt(
                'quiz/mcq_questions.txt',
                num_questions=num_questions,
                content=content  # Full content, no [:10000] truncation
            )
            
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.4,
                system_prompt="You are an expert tutor creating educational assessments.",
                response_schema=MCQQuizSchema,
                timeout=60.0
            )
            
            json_text = response.content

        # Parse response
        try:
            data = self._parse_json(json_text)
            
            # Handle wrapped response
            if isinstance(data, dict) and "questions" in data:
                questions_data = data["questions"]
            elif isinstance(data, list):
                questions_data = data
            else:
                raise ValueError("Invalid response format")

            # Validate and convert
            questions = [MCQQuestion(**item) for item in questions_data]
            
            # Validate each question has exactly one correct answer
            for q in questions:
                correct_count = sum(1 for opt in q.options if opt.is_correct)
                if correct_count != 1:
                    raise ValueError(f"Question must have exactly 1 correct answer, got {correct_count}")
            
            total_duration = (time.time() - start_time) * 1000
            logger.info("Successfully generated MCQ questions", extra={
                "component": "quiz_generator",
                "count": len(questions),
                "total_duration_ms": round(total_duration, 2),
                "used_cache": cache_name is not None
            })
            return questions

        except Exception as e:
            logger.error("Error parsing %s", "MCQ questions", extra={"component": "quiz_generator", "error": str(e)})
            raise ValueError(f"Failed to generate MCQ quiz: {str(e)}")
