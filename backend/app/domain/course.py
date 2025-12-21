# backend/app/domain/course.py
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from typing import List, Optional
from uuid import UUID, uuid4

@dataclass
class Course:
    """
    Course domain entity.
    Acts as a folder/container for multiple exams (study materials).
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)

    # Basic info
    title: str = ""
    subject: str = ""
    description: Optional[str] = None
    
    # Semester info
    semester_start: Optional[date] = None
    semester_end: Optional[date] = None
    
    # Status
    is_archived: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Aggregated stats (will be populated by repository/service)
    exam_count: int = 0
    topic_count: int = 0
    completed_topics: int = 0
    due_flashcards_count: int = 0
    total_actual_study_minutes: int = 0
    total_planned_study_minutes: int = 0
    average_difficulty: float = 0.0

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate course data"""
        if not self.title or len(self.title.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")

        if not self.subject or len(self.subject.strip()) < 2:
            raise ValueError("Subject must be at least 2 characters")

    def archive(self):
        """Archive course"""
        self.is_archived = True
        self.updated_at = datetime.now(timezone.utc)

    def unarchive(self):
        """Unarchive course"""
        self.is_archived = False
        self.updated_at = datetime.now(timezone.utc)

    def get_progress_percentage(self) -> float:
        """Calculate overall progress across all exams in the course"""
        if self.topic_count == 0:
            return 0.0
        return (self.completed_topics / self.topic_count) * 100
