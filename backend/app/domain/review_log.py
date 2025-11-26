from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass
class ReviewLog:
    """
    Log of a single review event.
    Used for analytics (retention curves, history).
    """
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    review_item_id: UUID = field(default_factory=uuid4)
    
    rating: int = 0  # 1-4
    review_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Snapshot of FSRS state at time of review
    interval_days: int = 0  # Actual days since last review
    scheduled_days: int = 0 # What was scheduled
    stability: float = 0.0
    difficulty: float = 0.0
    
    review_duration_ms: int = 0 # Time taken to answer
