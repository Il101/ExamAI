import json
import logging
from typing import List, Any

from pydantic import BaseModel, Field

from app.integrations.llm.base import LLMProvider
from app.core.config import settings
from google.genai import types
import asyncio

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
        # NOTE: We intentionally do NOT use the cache here. 
        # The flashcards are generated from the provided 'content' string (the topic summary),
        # not the entire book. Passing the massive cache + the content causing redundancy 
        # and 504 timeouts (RPC failures) in Gemini.
        
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
        current_model = settings.GEMINI_MODEL
        
        for attempt in range(max_retries):
            try:
                # Generate with AGGRESSIVE timeout (50s) to fail fast on stuck requests
                # Normal generation takes ~15s. If > 50s, it's likely stuck -> retry immediately.
                # Use GeminiProvider.generate for robust retries + counting
                llm_response = await self.llm.generate(
                    prompt=prompt,
                    temperature=0.3,
                    system_prompt="You are an expert tutor creating study materials.",
                    response_mime_type="application/json",
                    # Timeout handled by GeminiProvider (180s) or passing explicit
                    timeout=120.0
                )
                
                json_text = llm_response.content

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
                    if ("503" in error_msg or "overloaded" in error_msg) and current_model != settings.GEMINI_FALLBACK_MODEL:
                        logger.warning(
                            f"Flashcard generation overload on {current_model}, switching to fallback {settings.GEMINI_FALLBACK_MODEL}",
                            extra={"component": "quiz_generator"}
                        )
                        self.llm.model_name = settings.GEMINI_FALLBACK_MODEL
                        current_model = settings.GEMINI_FALLBACK_MODEL
                    
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

    async def generate_mcq_quiz(
        self, 
        content: str, 
        num_questions: int = 5
    ) -> List[MCQQuestion]:
        """
        Generate multiple choice questions from the provided content.
        
        Args:
            content: Study material text (from topic content)
            num_questions: Number of questions to generate (1-10)
        
        Returns:
            List of MCQQuestion objects with questions, options, and explanations
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
        current_model = settings.GEMINI_MODEL
        json_text = None
        
        for attempt in range(max_retries):
            try:
                # Load prompt with full content
                prompt = load_prompt(
                    'quiz/mcq_questions.txt',
                    num_questions=num_questions,
                    content=content
                )
                
                # Generate with structured output
                config = types.GenerateContentConfig(
                    temperature=0.4,
                    response_mime_type="application/json",
                    response_schema=MCQQuizSchema,
                    system_instruction="You are an expert tutor creating educational assessments.",
                )
                
                logger.debug("Calling Gemini API for MCQ generation", extra={
                    "component": "quiz_generator",
                    "model": current_model,
                    "num_questions": num_questions
                })
                
                api_start = time.time()
                response = await asyncio.wait_for(
                    self.llm.client.aio.models.generate_content(
                        model=current_model,
                        contents=prompt,
                        config=config
                    ),
                    timeout=50.0
                )
                api_duration = (time.time() - api_start) * 1000
                
                logger.info("Received MCQ response from Gemini API", extra={
                    "component": "quiz_generator",
                    "api_duration_ms": round(api_duration, 2),
                    "response_length": len(response.text) if response.text else 0
                })
                
                json_text = response.text
                
                # Success - break retry loop
                break
                
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
                    if ("503" in error_msg or "overloaded" in error_msg) and current_model != settings.GEMINI_FALLBACK_MODEL:
                        logger.warning(
                            f"MCQ generation overload on {current_model}, switching to fallback {settings.GEMINI_FALLBACK_MODEL}",
                            extra={"component": "quiz_generator"}
                        )
                        current_model = settings.GEMINI_FALLBACK_MODEL

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
        
        # Check if we have a response
        if not json_text:
            raise RuntimeError("Failed to generate MCQ quiz after all retries")
        
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
            questions = []
            for idx, q_data in enumerate(questions_data):
                try:
                    # Handle different formats from LLM
                    if isinstance(q_data.get("options"), dict):
                        # Options as {A: text, B: text, ...}
                        options = [
                            MCQOption(
                                text=q_data["options"].get(letter, ""),
                                is_correct=(letter == q_data["correct"])
                            )
                            for letter in ["A", "B", "C", "D"]
                            if letter in q_data["options"]
                        ]
                    elif isinstance(q_data.get("options"), list):
                        # Options as list of objects
                        options = [
                            MCQOption(
                                text=opt.get("text", opt) if isinstance(opt, dict) else opt,
                                is_correct=opt.get("is_correct", False) if isinstance(opt, dict) else False
                            )
                            for opt in q_data["options"]
                        ]
                    else:
                        raise ValueError(f"Invalid options format in question {idx}")
                    
                    # Handle explanation formats
                    explanation_data = q_data.get("explanation", {})
                    if isinstance(explanation_data, dict):
                        explanation = explanation_data.get("correct", "")
                    elif isinstance(explanation_data, str):
                        explanation = explanation_data
                    else:
                        explanation = ""
                    
                    question = MCQQuestion(
                        question=q_data["question"],
                        options=options,
                        explanation=explanation
                    )
                    questions.append(question)
                    
                except (KeyError, ValueError) as parse_error:
                    logger.warning(f"Skipping malformed question {idx}: {parse_error}", extra={"component": "quiz_generator"})
                    continue
            
            if not questions:
                raise ValueError("No valid questions could be parsed from response")
            
            duration = time.time() - start_time
            logger.info(
                f"Successfully generated {len(questions)} MCQ questions in {duration:.2f}s",
                extra={
                    "component": "quiz_generator",
                    "duration_seconds": round(duration, 2),
                    "questions_count": len(questions)
                }
            )
            
            return questions
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in MCQ response: {e}", extra={"component": "quiz_generator", "json_text": json_text[:500]})
            raise ValueError(f"Invalid JSON in LLM response: {e}")
        except Exception as e:
            logger.error(f"Error parsing MCQ response: {e}", extra={"component": "quiz_generator"})
            raise
