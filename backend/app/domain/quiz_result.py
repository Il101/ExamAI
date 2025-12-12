from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass
class QuizResult:
    """Domain entity for quiz result"""

    id: UUID
    user_id: UUID
    topic_id: UUID
    questions_total: int
    questions_correct: int
    completed_at: datetime
    created_at: datetime

    @property
    def score_percentage(self) -> float:
        """Calculate score as percentage"""
        if self.questions_total == 0:
            return 0.0
        return (self.questions_correct / self.questions_total) * 100

    @property
    def is_passing(self) -> bool:
        """Check if score is passing (>= 60%)"""
        return self.score_percentage >= 60.0
