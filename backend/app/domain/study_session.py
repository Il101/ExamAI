# backend/app/domain/study_session.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4


@dataclass
class StudySession:
    """
    Study session for tracking user's learning activity.
    Supports Pomodoro technique.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    exam_id: UUID = field(default_factory=uuid4)

    # Session info
    started_at: datetime = field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None

    # Pomodoro settings
    pomodoro_duration_minutes: int = 25
    break_duration_minutes: int = 5
    pomodoros_completed: int = 0

    # Topics studied in this session
    topic_ids: List[UUID] = field(default_factory=list)

    # Review statistics
    items_reviewed: int = 0
    items_correct: int = 0
    items_failed: int = 0

    is_active: bool = True

    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.pomodoro_duration_minutes <= 0:
            raise ValueError("Pomodoro duration must be positive")

    # Business logic

    def complete_pomodoro(self):
        """Mark one pomodoro as completed"""
        if not self.is_active:
            raise ValueError("Cannot complete pomodoro in inactive session")

        self.pomodoros_completed += 1

    def record_review(self, is_correct: bool):
        """Record a review item result"""
        if not self.is_active:
            raise ValueError("Cannot record review in inactive session")

        self.items_reviewed += 1
        if is_correct:
            self.items_correct += 1
        else:
            self.items_failed += 1

    def add_topic(self, topic_id: UUID):
        """Add topic to study session"""
        if topic_id not in self.topic_ids:
            self.topic_ids.append(topic_id)

    def end_session(self):
        """End study session"""
        if not self.is_active:
            raise ValueError("Session already ended")

        self.is_active = False
        self.ended_at = datetime.utcnow()

    def get_duration_minutes(self) -> int:
        """Get session duration in minutes"""
        end_time = self.ended_at or datetime.utcnow()
        duration = end_time - self.started_at
        return int(duration.total_seconds() / 60)

    def get_success_rate(self) -> float:
        """Get review success rate"""
        if self.items_reviewed == 0:
            return 0.0
        return self.items_correct / self.items_reviewed

    def get_next_break_time(self) -> datetime:
        """Calculate when next break should start"""
        next_pomodoro_end = self.started_at + timedelta(
            minutes=(self.pomodoros_completed + 1) * self.pomodoro_duration_minutes
        )
        return next_pomodoro_end

    def should_take_long_break(self) -> bool:
        """Check if user should take long break (after 4 pomodoros)"""
        return self.pomodoros_completed > 0 and self.pomodoros_completed % 4 == 0
