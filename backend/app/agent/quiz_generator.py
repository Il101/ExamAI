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


class QuizGenerator:
    """
    Generates study materials (flashcards/quizzes) from content using AI.
    Uses Gemini Structured Output for reliable generation.
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def generate_flashcards(self, content: str, num_cards: int = 5) -> List[FlashcardSchema]:
        """
        Generate flashcards from the provided content.

        Args:
            content: Study material text
            num_cards: Target number of cards to generate

        Returns:
            List of FlashcardSchema objects
        """
        
        prompt = f"""You are an expert tutor. Create {num_cards} high-quality flashcards based on the text below.

**Content:**
```
{content[:10000]}  # Limit context window
```

**Requirements:**
- Create exactly {num_cards} cards
- "Front" should be a clear question or concept
- "Back" should be a concise but complete answer
- Focus on key facts, definitions, and relationships
- Avoid trivial questions
"""

        print(f"[QuizGenerator] Generating {num_cards} flashcards...")
        
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            system_prompt="You are an expert tutor creating study materials.",
            response_schema=FlashcardSetSchema,
        )

        # Parse response
        try:
            # Clean response if needed (though response_schema usually handles it)
            json_text = response.content.strip()
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
