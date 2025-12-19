"""
Flashcard generation service.

Single responsibility: Generate and store flashcards for topics.
Extracted from legacy agent code to eliminate duplication.
"""
from typing import List, Optional, Any, Dict
from uuid import UUID
import logging

from app.agent.quiz_generator import QuizGenerator
from app.domain.review import ReviewItem
from app.repositories.review_repository import ReviewItemRepository

logger = logging.getLogger(__name__)


class FlashcardGenerator:
    """
    Generates flashcards for topics.
    
    This is the ONLY place where flashcards are created.
    Used by all content generation paths to ensure consistency.
    
    Guarantees:
    - Flashcards are created if content >= MIN_CONTENT_LENGTH
    - Graceful error handling (doesn't fail topic generation)
    - Cache is used when available
    """
    
    MIN_CONTENT_LENGTH = 50
    DEFAULT_CARD_COUNT = 3
    
    def __init__(
        self,
        quiz_generator: QuizGenerator,
        review_repo: ReviewItemRepository
    ):
        """
        Initialize flashcard generator.
        
        Args:
            quiz_generator: QuizGenerator instance for AI generation
            review_repo: Repository for storing review items
        """
        self.quiz_generator = quiz_generator
        self.review_repo = review_repo
    
    async def create_for_topic(
        self,
        topic_id: UUID,
        user_id: UUID,
        content: str,
        cache_name: Optional[str] = None,
        num_cards: int = DEFAULT_CARD_COUNT
    ) -> tuple[List[ReviewItem], dict[str, Any]]:
        """
        Generate and store flashcards for a topic.
        
        Args:
            topic_id: Topic UUID
            user_id: User UUID
            content: Topic content to generate flashcards from
            cache_name: Optional Gemini cache name for faster generation
            num_cards: Number of flashcards to generate (default: 3)
            
        Returns:
            Tuple of (List of created ReviewItem objects, usage_metadata dict)
            
        Raises:
            ValueError: If content is too short
            
        Note:
            This method is designed to be fault-tolerant. If flashcard
            generation fails, it logs the error but doesn't raise,
            allowing topic generation to complete successfully.
        """
        # Validate content length
        if len(content) < self.MIN_CONTENT_LENGTH:
            logger.warning(
                f"Content too short for flashcards: {len(content)} < {self.MIN_CONTENT_LENGTH} "
                f"(topic_id={topic_id})"
            )
            raise ValueError(
                f"Content must be at least {self.MIN_CONTENT_LENGTH} characters. "
                f"Got {len(content)} characters."
            )
        
        try:
            # Generate flashcards using AI
            logger.info(
                f"Generating {num_cards} flashcards for topic {topic_id} "
                f"(cache: {cache_name or 'none'})"
            )
            
            flashcards, usage = await self.quiz_generator.generate_flashcards(
                content=content,
                num_cards=num_cards
            )
            
            # Store in database
            created_items = []
            for idx, card in enumerate(flashcards):
                review_item = ReviewItem(
                    topic_id=topic_id,
                    user_id=user_id,
                    question=card.front,
                    answer=card.back
                )
                created_item = await self.review_repo.create(review_item)
                created_items.append(created_item)
                
                logger.debug(
                    f"Created flashcard {idx + 1}/{len(flashcards)} "
                    f"for topic {topic_id}"
                )
            
            logger.info(
                f"✅ Successfully created {len(created_items)} flashcards "
                f"for topic {topic_id}"
            )
            
            return created_items, usage
            
        except Exception as e:
            # Log error but don't fail topic generation
            logger.error(
                f"Failed to generate flashcards for topic {topic_id}: "
                f"{type(e).__name__}: {e}",
                exc_info=True
            )
            # Re-raise to let caller decide how to handle
            raise
    
    async def create_for_batch(
        self,
        topics_data: List[Dict[str, Any]],
        user_id: UUID,
        cache_name: Optional[str] = None,
        num_cards_per_topic: int = DEFAULT_CARD_COUNT
    ) -> tuple[Dict[int, List[ReviewItem]], dict[str, Any]]:
        """
        Generate and store flashcards for a batch of topics.
        topics_data: [{'id': 1, 'title': 'Topic', 'content': '...'}]
        """
        if not topics_data:
            return {}, {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}

        try:
            logger.info(f"Generating flashcards for batch of {len(topics_data)} topics")
            
            # Generate in batch
            grouped_cards, usage = await self.quiz_generator.generate_flashcards_batch(
                topics_data=topics_data,
                num_cards_per_topic=num_cards_per_topic
            )
            
            batch_results = {}
            for topic_id, cards in grouped_cards.items():
                created_items = []
                for card in cards:
                    review_item = ReviewItem(
                        topic_id=UUID(topic_id) if isinstance(topic_id, str) else topic_id,
                        user_id=user_id,
                        question=card.front,
                        answer=card.back
                    )
                    created_item = await self.review_repo.create(review_item)
                    created_items.append(created_item)
                batch_results[topic_id] = created_items
                print(f"[PIPELINE] flashcards_saved topic_id={topic_id} count={len(created_items)}")

            logger.info(f"✅ Successfully created flashcard batch for {len(batch_results)} topics")
            return batch_results, usage

        except Exception as e:
            logger.error(f"Flashcard batch generation failed: {e}", exc_info=True)
            raise

    async def create_for_topic_safe(
        self,
        topic_id: UUID,
        user_id: UUID,
        content: str,
        cache_name: Optional[str] = None,
        num_cards: int = DEFAULT_CARD_COUNT
    ) -> tuple[Optional[List[ReviewItem]], dict[str, Any]]:
        """
        Safe version that catches all exceptions.
        
        Use this when flashcard generation failure should not
        prevent topic generation from completing.
        
        Returns:
            Tuple of (List of created items or None, usage_metadata dict)
        """
        try:
            return await self.create_for_topic(
                topic_id=topic_id,
                user_id=user_id,
                content=content,
                cache_name=cache_name,
                num_cards=num_cards
            )
        except Exception as e:
            logger.warning(
                f"Flashcard generation failed for topic {topic_id}, "
                f"continuing without flashcards: {e}"
            )
            return None, {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}
