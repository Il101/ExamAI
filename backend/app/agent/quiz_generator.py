import json
from typing import List

from pydantic import BaseModel, Field

from app.integrations.llm.base import LLMProvider


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
        cache_name: str = None
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
        
        print(f"[QuizGenerator] Generating {num_cards} flashcards...")
        
        # Use cache if available, otherwise use content directly
        if cache_name:
            # Use cache - no content truncation needed
            prompt = load_prompt(
                'quiz/flashcards.txt',
                num_cards=num_cards,
                content="[Content is available in cache context]"
            )
            
            # Call with cache
            response = await self.llm.client.aio.models.generate_content(
                model=cache_name,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )
            
            json_text = response.text
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
            # Clean response
            json_text = json_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith("```"):
                json_text = json_text[3:-3].strip()

            data = json.loads(json_text)
            
            # Handle wrapped response
            if isinstance(data, dict) and "cards" in data:
                cards_data = data["cards"]
            elif isinstance(data, list):
                cards_data = data
            else:
                raise ValueError("Invalid response format")

            # Validate and convert
            flashcards = [FlashcardSchema(**item) for item in cards_data]
            
            print(f"[QuizGenerator] Generated {len(flashcards)} flashcards")
            return flashcards

        except Exception as e:
            print(f"[QuizGenerator] Error parsing flashcards: {e}")
            # Fallback or re-raise? For now re-raise to see errors
            raise ValueError(f"Failed to generate flashcards: {str(e)}")

    async def generate_mcq_quiz(
        self, 
        content: str, 
        num_questions: int = 5,
        cache_name: str = None
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
        
        print(f"[QuizGenerator] Generating {num_questions} MCQ questions...")
        
        # Use cache if available, otherwise use content directly
        if cache_name:
            # Use cache - no content truncation needed
            prompt = load_prompt(
                'quiz/mcq_questions.txt',
                num_questions=num_questions,
                content="[Content is available in cache context]"
            )
            
            # Call with cache
            response = await self.llm.client.aio.models.generate_content(
                model=cache_name,
                contents=[{"role": "user", "parts": [{"text": prompt}]}]
            )
            
            json_text = response.text
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
            json_text = json_text.strip()
            if json_text.startswith("```json"):
                json_text = json_text[7:-3].strip()
            elif json_text.startswith("```"):
                json_text = json_text[3:-3].strip()

            data = json.loads(json_text)
            
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
            
            print(f"[QuizGenerator] Generated {len(questions)} MCQ questions")
            return questions

        except Exception as e:
            print(f"[QuizGenerator] Error parsing MCQ questions: {e}")
            raise ValueError(f"Failed to generate MCQ quiz: {str(e)}")

