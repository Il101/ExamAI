# backend/app/domain/topic.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID, uuid4

DifficultyLevel = Literal[1, 2, 3, 4, 5]


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
    content: str = ""  # Generated AI content

    # Metadata
    order_index: int = 0  # Position in exam structure
    difficulty_level: DifficultyLevel = 3  # 1=easy, 5=hard

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    # Estimated study time (in minutes)
    estimated_study_minutes: int = 0

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate topic data"""
        if not self.topic_name or len(self.topic_name.strip()) < 2:
            raise ValueError("Topic name must be at least 2 characters")

        if not self.content or len(self.content.strip()) < 50:
            raise ValueError("Topic content must be at least 50 characters")

        if not 1 <= self.difficulty_level <= 5:
            raise ValueError("Difficulty must be between 1 and 5")

    # Business logic

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
