"""
Unified content generation system.

This package provides a single, consistent way to generate exam content.

Components:
- FlashcardGenerator: Creates flashcards for topics
- TopicContentGenerator: Generates content for a single topic

Usage:
    from app.services.content_generation import TopicContentGenerator
    
    # Content generation is handled by Celery tasks
    # using TopicContentGenerator directly
"""

from app.services.content_generation.flashcard_generator import FlashcardGenerator
from app.services.content_generation.topic_generator import TopicContentGenerator

__all__ = [
    "FlashcardGenerator",
    "TopicContentGenerator",
]
