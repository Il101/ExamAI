# backend/app/domain/review.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Literal
from uuid import UUID, uuid4
import math

# FSRS Ratings
Rating = Literal[1, 2, 3, 4]
# 1 = Again (Forgot)
# 2 = Hard (Remembered with effort)
# 3 = Good (Remembered)
# 4 = Easy (Remembered easily)

CardState = Literal["new", "learning", "review", "relearning"]

@dataclass
class ReviewItem:
    """
    Review item for spaced repetition (FSRS algorithm).
    Each topic can have multiple review items (flashcards, questions).
    """
    
    id: UUID = field(default_factory=uuid4)
    topic_id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    
    # Question/Answer
    question: str = ""
    answer: str = ""
    
    # FSRS Parameters
    stability: float = 0.0       # S: days to 90% retention
    difficulty: float = 0.0      # D: 0-10 scale
    elapsed_days: int = 0        # Days since last review
    scheduled_days: int = 0      # Scheduled interval
    reps: int = 0                # Total review count
    lapses: int = 0              # Number of failures
    state: CardState = "new"     # Current state
    
    # Learning Steps (Anki-style)
    # Default: 1 min, 10 min (represented in minutes)
    learning_steps: list[int] = field(default_factory=lambda: [1, 10])
    current_step_index: int = 0  # Current step in learning_steps
    
    # Review history
    next_review_date: datetime = field(default_factory=datetime.utcnow)
    last_reviewed_at: Optional[datetime] = None
    last_review_rating: Optional[Rating] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    # Default FSRS Weights (v4.5 optimized on Anki dataset)
    # Can be overridden per user in future
    _w: list[float] = field(default_factory=lambda: [
        0.4, 0.6, 2.4, 5.8,    # Initial stability for ratings 1-4
        4.93, 0.94, 0.86,       # Difficulty factors
        0.01, 1.49, 0.14,       # Stability increase factors
        0.94, 2.18, 0.05,       # Difficulty modifiers
        0.34, 1.26, 0.29,       # Advanced stability
        2.61                    # Decay factor
    ])

    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate review item"""
        if not self.question or len(self.question.strip()) < 5:
            raise ValueError("Question must be at least 5 characters")
        
        if not self.answer or len(self.answer.strip()) < 2:
            raise ValueError("Answer must be at least 2 characters")

    # --- FSRS Logic ---

    def review(self, rating: Rating, review_time: Optional[datetime] = None) -> datetime:
        """
        Process review using FSRS algorithm with Anki-style learning steps.
        Updates stability, difficulty, and schedules next review.
        """
        if review_time is None:
            review_time = datetime.utcnow()
            
        if self.last_reviewed_at:
            self.elapsed_days = (review_time - self.last_reviewed_at).days
        else:
            self.elapsed_days = 0

        # Handle Learning / Relearning Steps
        if self.state in ("new", "learning", "relearning"):
            previous_state = self.state # Remember state before update
            
            if self.state == "new":
                self._init_fsrs(rating)
                self.state = "learning"
                self.current_step_index = 0

            if rating == 1: # Again
                self.current_step_index = 0
                step_minutes = self.learning_steps[0]
                self.next_review_date = review_time + timedelta(minutes=step_minutes)
                self.state = "learning" # Stay in learning
                
                # Only count lapse if we were not new
                if previous_state != "new": 
                     self.lapses += 1
            
            elif rating == 2: # Hard
                # Repeat current step
                step_minutes = self.learning_steps[self.current_step_index]
                self.next_review_date = review_time + timedelta(minutes=step_minutes)
            
            elif rating == 3: # Good
                self.current_step_index += 1
                if self.current_step_index < len(self.learning_steps):
                    # Move to next step
                    step_minutes = self.learning_steps[self.current_step_index]
                    self.next_review_date = review_time + timedelta(minutes=step_minutes)
                else:
                    # Graduate to Review
                    self.state = "review"
                    self.scheduled_days = self._calculate_next_interval(self.stability)
                    self.next_review_date = review_time + timedelta(days=self.scheduled_days)
            
            elif rating == 4: # Easy
                # Immediately graduate
                self.state = "review"
                self.scheduled_days = self._calculate_next_interval(self.stability)
                # Easy bonus could be applied here if desired
                self.next_review_date = review_time + timedelta(days=self.scheduled_days)

            # Update FSRS parameters even during learning (optional but good for data)
            # But NOT if we just initialized it in this same call
            if self.state != "new" and previous_state != "new": 
                 self._update_fsrs(rating)

        else:
            # Normal Review State
            self._update_fsrs(rating)

            # Calculate next interval
            if rating == 1:
                # Lapse -> Relearning
                self.lapses += 1
                self.state = "relearning"
                self.current_step_index = 0
                step_minutes = self.learning_steps[0]
                self.next_review_date = review_time + timedelta(minutes=step_minutes)
                self.scheduled_days = 0 # Reset scheduled days for relearning
            else:
                self.scheduled_days = self._calculate_next_interval(self.stability)
                self.next_review_date = review_time + timedelta(days=self.scheduled_days)
        
        # Update metadata
        self.reps += 1
        self.last_review_rating = rating
        self.last_reviewed_at = review_time
        
        return self.next_review_date

    def _init_fsrs(self, rating: int):
        """Initialize stability and difficulty for new cards"""
        # Initial stability based on first rating
        self.stability = max(0.1, self._w[rating - 1])
        
        # Initial difficulty
        # D0 = w4 - (G-3) * w5
        self.difficulty = self._w[4] - (rating - 3) * self._w[5]
        self.difficulty = max(1, min(10, self.difficulty))

    def _update_fsrs(self, rating: int):
        """Update stability and difficulty for existing cards"""
        retrievability = self._calculate_retrievability(self.stability, self.elapsed_days)
        
        # 1. Next Difficulty
        # D' = D - w6 * (rating - 3)
        next_d = self.difficulty - self._w[6] * (rating - 3)
        # Mean reversion: D' = D' + w7 * (5 - D')
        next_d = next_d + self._w[7] * (5 - next_d)
        self.difficulty = max(1, min(10, next_d))

        # 2. Next Stability
        if rating == 1: # Again
            # S' = w11 * D^(-w12) * ((S+1)^w13) * exp(w14 * (1-R))
             self.stability = (
                self._w[11] *
                (self.difficulty ** -self._w[12]) *
                ((self.stability + 1) ** self._w[13]) *
                math.exp(self._w[14] * (1 - retrievability))
            )
        else:
            # Successful review
            # S_new = S * (1 + exp(w8) * (11-D) * S^-w9 * (exp((1-R)*w10)-1) * modifiers)
            increase = (math.exp(self._w[8]) * 
                       (11 - self.difficulty) * 
                       self.stability ** -self._w[9] * 
                       (math.exp((1 - retrievability) * self._w[10]) - 1))
            
            if rating == 2: # Hard
                increase *= self._w[15]
            elif rating == 4: # Easy
                increase *= self._w[16]
            
            self.stability = self.stability * (1 + increase)

        self.stability = max(0.1, self.stability)

    def _calculate_retrievability(self, stability: float, elapsed_days: int) -> float:
        """R(t) = (1 + t / (9 * S))^-1"""
        if stability <= 0:
            return 0.0
        return (1 + elapsed_days / (9 * stability)) ** (-1)

    def _calculate_next_interval(self, stability: float, desired_retention: float = 0.9) -> int:
        """
        Calculate interval for target retention.
        I = 9 * S * (1/R - 1)
        """
        if stability <= 0:
            return 1
        interval = 9 * stability * (1 / desired_retention - 1)
        return max(1, round(interval))

    def is_due(self) -> bool:
        """Check if review is due"""
        return datetime.utcnow() >= self.next_review_date
    
    def get_success_rate(self) -> float:
        """Get success rate (0.0 to 1.0)"""
        if self.reps == 0:
            return 0.0
        # Success is any rating > 1 (Again)
        successful_reviews = self.reps - self.lapses
        return successful_reviews / self.reps

    def reset(self):
        """Reset review progress"""
        self.stability = 0.0
        self.difficulty = 0.0
        self.elapsed_days = 0
        self.scheduled_days = 0
        self.reps = 0
        self.lapses = 0
        self.state = "new"
        self.current_step_index = 0
        self.next_review_date = datetime.utcnow()
        self.last_reviewed_at = None
        self.last_review_rating = None
