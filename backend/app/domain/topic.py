# backend/app/domain/topic.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

DifficultyLevel = Literal[1, 2, 3, 4, 5]
TopicStatus = Literal["pending", "generating", "ready", "failed"]


@dataclass
class Topic:
    """
    Topic (exam section) domain entity.
    Represents one generated topic within an exam.
    """

    id: UUID = field(default_factory=uuid4)
    exam_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)

    # Content
    topic_name: str = ""
    content: str = ""  # Generated AI content (Markdown for backward compatibility)
    content_blocknote: Optional[dict] = None  # BlockNote JSON format
    content_markdown_backup: Optional[str] = None  # Backup of original Markdown
    file_context: Optional[str] = None  # Relevant file chunk for this topic
    quiz_data: Optional[dict] = None  # Cached MCQ quiz questions
    
    # Dynamic counts (not stored in DB, computed)
    flashcard_count: int = 0

    # Metadata
    status: TopicStatus = "pending"  # Generation status
    order_index: int = 0  # Position in exam structure
    generation_priority: int = 0  # Lower = higher priority
    difficulty_level: DifficultyLevel = 3  # 1=easy, 5=hard

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Estimated study time (in minutes)
    estimated_study_minutes: int = 0

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate topic data"""
        if not self.topic_name or len(self.topic_name.strip()) < 2:
            raise ValueError("Topic name must be at least 2 characters")

        # Content validation only for ready topics
        if self.status == "ready" and (not self.content or len(self.content.strip()) < 50):
            raise ValueError("Ready topic must have content (at least 50 characters)")

        if not 1 <= self.difficulty_level <= 5:
            raise ValueError("Difficulty must be between 1 and 5")

    # Business logic
    
    def can_generate(self) -> bool:
        """Check if topic can start generation"""
        return self.status in ["pending", "failed"]
    
    def start_generation(self):
        """Mark topic as generating"""
        if not self.can_generate():
            raise ValueError(f"Cannot start generation: status={self.status}")
        
        self.status = "generating"
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_as_ready(self, content: str):
        """Mark topic as ready with generated content"""
        if self.status != "generating":
            raise ValueError("Can only mark generating topics as ready")
        
        self.content = content
        self.status = "ready"
        self.updated_at = datetime.now(timezone.utc)
    
    def mark_as_failed(self, error_message: Optional[str] = None):
        """Mark topic generation as failed"""
        if self.status != "generating":
            raise ValueError("Can only mark generating topics as failed")
        
        self.status = "failed"
        self.updated_at = datetime.now(timezone.utc)

    def estimate_study_time(self) -> int:
        """
        Estimate study time based on content length and difficulty.
        Formula: (words / reading_speed) * difficulty_multiplier
        """
        words = len(self.content.split())
        reading_speed = 200  # words per minute
        base_time = words / reading_speed

        # Difficulty multipliers
        multipliers = {1: 1.0, 2: 1.2, 3: 1.5, 4: 1.8, 5: 2.0}

        estimated = int(base_time * multipliers[self.difficulty_level])
        self.estimated_study_minutes = max(5, estimated)  # Minimum 5 minutes

        return self.estimated_study_minutes

    def get_word_count(self) -> int:
        """Get word count of content"""
        return len(self.content.split())

    def get_preview(self, max_chars: int = 150) -> str:
        """Get content preview for UI"""
        if len(self.content) <= max_chars:
            return self.content
        return self.content[:max_chars] + "..."
