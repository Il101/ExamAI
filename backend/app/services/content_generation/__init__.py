"""
Unified content generation system.

This package provides a single, consistent way to generate exam content,
replacing multiple legacy paths with a clean, testable architecture.

Components:
- FlashcardGenerator: Creates flashcards for topics
- TopicContentGenerator: Generates content for a single topic
- GenerationStrategy: Batch vs Incremental generation strategies
- ContentGenerationOrchestrator: Main coordinator

Usage:
    from app.services.content_generation import ContentGenerationOrchestrator
    
    orchestrator = get_orchestrator()
    await orchestrator.generate_exam_content(exam, mode=GenerationMode.BATCH)
"""

from app.services.content_generation.flashcard_generator import FlashcardGenerator
from app.services.content_generation.topic_generator import TopicContentGenerator
from app.services.content_generation.strategies import (
    GenerationStrategy,
    BatchStrategy,
    IncrementalStrategy,
    GenerationMode
)
from app.services.content_generation.orchestrator import ContentGenerationOrchestrator

__all__ = [
    "FlashcardGenerator",
    "TopicContentGenerator",
    "GenerationStrategy",
    "BatchStrategy",
    "IncrementalStrategy",
    "GenerationMode",
    "ContentGenerationOrchestrator",
]
