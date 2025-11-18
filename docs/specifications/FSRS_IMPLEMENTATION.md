# FSRS (Free Spaced Repetition Scheduler) Implementation Guide

## Why FSRS over SM-2?

**Current State**: ExamAI uses SM-2 algorithm (1987)  
**Problem**: SM-2 is reliable but outdated - uses fixed parameters for all users  
**Solution**: FSRS (2023) - adaptive algorithm that personalizes to each user's memory

### Key Advantages

| Feature | SM-2 | FSRS |
|---------|------|------|
| **Personalization** | Fixed parameters | Learns from user's review history |
| **Accuracy** | ±20% prediction error | ±12% prediction error |
| **Forgetting Curve** | Exponential (simplified) | Power-law (research-backed) |
| **Parameter Updates** | Manual | Automatic optimization |
| **Data Required** | None | Improves with usage |
| **Anki Support** | Legacy | Default since 2023 |

---

## FSRS Algorithm Overview

### Core Concept

FSRS models memory retention using **4 parameters per card**:

1. **Stability (S)**: How long memory lasts before 90% retention
2. **Difficulty (D)**: How hard the card is to remember (0-10)
3. **Retrievability (R)**: Current probability of recall (0-1)
4. **Elapsed Days**: Days since last review

### Formula

```
R(t) = (1 + t/(9*S))^(-1)

Where:
- R(t) = Retrievability at time t
- t = days since last review
- S = Stability (days to reach 90% retention)
```

### State Machine

```
New Card
   ↓
Learning (1min, 10min)
   ↓
Young (stability < 21 days)
   ↓
Mature (stability ≥ 21 days)
   ↓
Relearning (if failed)
```

---

## Database Schema Changes

### Update `review_items` Table

```sql
-- Add FSRS parameters
ALTER TABLE review_items
  -- Remove SM-2 fields
  DROP COLUMN IF EXISTS easiness_factor,
  DROP COLUMN IF EXISTS repetitions,
  
  -- Add FSRS fields
  ADD COLUMN stability DECIMAL(10, 2) DEFAULT 0,  -- S: days to 90% retention
  ADD COLUMN difficulty DECIMAL(4, 2) DEFAULT 5,  -- D: 0-10 scale
  ADD COLUMN elapsed_days INTEGER DEFAULT 0,      -- Days since last review
  ADD COLUMN scheduled_days INTEGER DEFAULT 0,    -- Scheduled interval
  ADD COLUMN reps INTEGER DEFAULT 0,              -- Total review count
  ADD COLUMN lapses INTEGER DEFAULT 0,            -- Number of failures
  ADD COLUMN state VARCHAR(20) DEFAULT 'new',     -- new, learning, review, relearning
  ADD COLUMN last_review_rating INTEGER;          -- 1=again, 2=hard, 3=good, 4=easy

-- Add index for efficient queries
CREATE INDEX idx_review_items_next_review_fsrs 
  ON review_items(user_id, next_review_date) 
  WHERE state IN ('review', 'relearning');
```

### New Table: `fsrs_parameters`

```sql
CREATE TABLE fsrs_parameters (
  id SERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  
  -- 17 FSRS model weights (updated via optimization)
  w JSONB NOT NULL DEFAULT '[
    0.4, 0.6, 2.4, 5.8,    -- Initial stability for [Again, Hard, Good, Easy]
    4.93, 0.94, 0.86,       -- Difficulty weights
    0.01, 1.49, 0.14,       -- Stability increase factors
    0.94, 2.18, 0.05,       -- Difficulty change rates
    0.34, 1.26, 0.29,       -- Advanced stability factors
    2.61                    -- Final stability weight
  ]'::jsonb,
  
  -- Metadata
  total_reviews INTEGER DEFAULT 0,
  last_optimized_at TIMESTAMP,
  optimization_loss DECIMAL(10, 4),  -- Model accuracy metric
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  
  UNIQUE(user_id)
);

-- Row-level security
ALTER TABLE fsrs_parameters ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can only access own FSRS parameters"
  ON fsrs_parameters FOR ALL
  USING (auth.uid() = user_id);
```

---

## Python Implementation

### Step 1: FSRS Service

```python
# backend/app/services/fsrs_service.py
from typing import List, Tuple
from datetime import datetime, timedelta
import math
import numpy as np


class FSRSService:
    """
    FSRS (Free Spaced Repetition Scheduler) implementation.
    Based on: https://github.com/open-spaced-repetition/fsrs4anki
    """
    
    # Default FSRS-4.5 parameters (optimized on Anki dataset)
    DEFAULT_WEIGHTS = [
        0.4, 0.6, 2.4, 5.8,    # Initial stability for ratings 1-4
        4.93, 0.94, 0.86,       # Difficulty factors
        0.01, 1.49, 0.14,       # Stability increase factors
        0.94, 2.18, 0.05,       # Difficulty modifiers
        0.34, 1.26, 0.29,       # Advanced stability
        2.61                    # Decay factor
    ]
    
    # Rating values: 1=Again, 2=Hard, 3=Good, 4=Easy
    RATING_AGAIN = 1
    RATING_HARD = 2
    RATING_GOOD = 3
    RATING_EASY = 4
    
    def __init__(self, weights: List[float] = None):
        """Initialize with custom or default weights"""
        self.w = weights or self.DEFAULT_WEIGHTS
    
    def calculate_retention(
        self,
        stability: float,
        elapsed_days: int
    ) -> float:
        """
        Calculate current retention/retrievability.
        
        Args:
            stability: Stability in days (S)
            elapsed_days: Days since last review (t)
        
        Returns:
            Retention probability (0-1)
        """
        if stability <= 0:
            return 0.0
        
        return (1 + elapsed_days / (9 * stability)) ** (-1)
    
    def init_stability(self, rating: int) -> float:
        """
        Calculate initial stability for new card.
        
        Args:
            rating: User rating (1-4)
        
        Returns:
            Initial stability in days
        """
        return max(0.1, self.w[rating - 1])
    
    def init_difficulty(self, rating: int) -> float:
        """
        Calculate initial difficulty for new card.
        
        Args:
            rating: User rating (1-4)
        
        Returns:
            Difficulty (0-10)
        """
        difficulty = self.w[4] - (rating - 3) * self.w[5]
        return max(1, min(10, difficulty))
    
    def next_stability(
        self,
        current_stability: float,
        difficulty: float,
        rating: int,
        retrievability: float
    ) -> float:
        """
        Calculate new stability after review.
        
        Args:
            current_stability: Current S
            difficulty: Current D (0-10)
            rating: User rating (1-4)
            retrievability: Current R (0-1)
        
        Returns:
            New stability
        """
        if rating == self.RATING_AGAIN:
            # Failed review: stability decreases
            new_s = (
                self.w[11] *
                current_stability ** self.w[12] *
                math.exp(self.w[13] * (difficulty - 1)) *
                math.exp(self.w[14] * (1 - retrievability))
            )
        else:
            # Successful review: stability increases
            hard_penalty = 1 if rating == self.RATING_HARD else 0
            easy_bonus = 1 if rating == self.RATING_EASY else 0
            
            new_s = (
                current_stability *
                (1 +
                 math.exp(self.w[8]) *
                 (11 - difficulty) *
                 current_stability ** -self.w[9] *
                 (math.exp((1 - retrievability) * self.w[10]) - 1) *
                 hard_penalty * self.w[15] +
                 easy_bonus * self.w[16]
                )
            )
        
        return max(0.1, new_s)
    
    def next_difficulty(
        self,
        current_difficulty: float,
        rating: int
    ) -> float:
        """
        Calculate new difficulty after review.
        
        Args:
            current_difficulty: Current D (0-10)
            rating: User rating (1-4)
        
        Returns:
            New difficulty
        """
        delta = self.w[6] * (rating - 3)
        new_d = current_difficulty - delta
        
        # Mean reversion: difficulty slowly trends to 5
        mean_reversion = self.w[7] * (5 - new_d)
        new_d += mean_reversion
        
        return max(1, min(10, new_d))
    
    def calculate_next_interval(
        self,
        stability: float,
        desired_retention: float = 0.9
    ) -> int:
        """
        Calculate optimal review interval.
        
        Args:
            stability: Current stability
            desired_retention: Target retention (default: 90%)
        
        Returns:
            Days until next review
        """
        if stability <= 0:
            return 1
        
        # Solve for t when R(t) = desired_retention
        interval = 9 * stability * (1 / desired_retention - 1)
        return max(1, round(interval))
    
    def get_next_intervals(
        self,
        stability: float,
        difficulty: float,
        retrievability: float,
        desired_retention: float = 0.9
    ) -> dict:
        """
        Calculate intervals for all 4 possible ratings.
        
        Returns:
            {
                "again": int,  # If user fails
                "hard": int,   # If hard to remember
                "good": int,   # Normal recall
                "easy": int    # Easy recall
            }
        """
        intervals = {}
        
        for rating in [self.RATING_AGAIN, self.RATING_HARD, 
                       self.RATING_GOOD, self.RATING_EASY]:
            new_s = self.next_stability(stability, difficulty, rating, retrievability)
            intervals[self._rating_to_name(rating)] = self.calculate_next_interval(
                new_s, desired_retention
            )
        
        return intervals
    
    def _rating_to_name(self, rating: int) -> str:
        """Convert rating number to name"""
        names = {1: "again", 2: "hard", 3: "good", 4: "easy"}
        return names.get(rating, "good")
    
    async def review_card(
        self,
        review_item: ReviewItem,
        rating: int,
        review_date: datetime = None
    ) -> ReviewItem:
        """
        Process review and update card parameters.
        
        Args:
            review_item: Current review item
            rating: User rating (1-4)
            review_date: Review timestamp (default: now)
        
        Returns:
            Updated review item
        """
        if review_date is None:
            review_date = datetime.utcnow()
        
        # Calculate elapsed time
        if review_item.last_reviewed_at:
            elapsed = (review_date - review_item.last_reviewed_at).days
        else:
            elapsed = 0
        
        # Initialize for new cards
        if review_item.state == "new":
            stability = self.init_stability(rating)
            difficulty = self.init_difficulty(rating)
            retrievability = 1.0  # Perfect retention at first review
            review_item.state = "learning"
        else:
            # Calculate current retention
            retrievability = self.calculate_retention(
                review_item.stability,
                elapsed
            )
            
            # Update parameters
            stability = self.next_stability(
                review_item.stability,
                review_item.difficulty,
                rating,
                retrievability
            )
            difficulty = self.next_difficulty(review_item.difficulty, rating)
        
        # Calculate next interval
        next_interval = self.calculate_next_interval(stability)
        
        # Update review item
        review_item.stability = stability
        review_item.difficulty = difficulty
        review_item.elapsed_days = elapsed
        review_item.scheduled_days = next_interval
        review_item.last_review_rating = rating
        review_item.last_reviewed_at = review_date
        review_item.next_review_date = review_date + timedelta(days=next_interval)
        review_item.reps += 1
        
        # Update state
        if rating == self.RATING_AGAIN:
            review_item.lapses += 1
            review_item.state = "relearning"
        elif stability >= 21:
            review_item.state = "review"  # Mature card
        else:
            review_item.state = "review"  # Young card
        
        return review_item
```

### Step 2: Integration with StudyService

```python
# backend/app/services/study_service.py

class StudyService:
    """Study session service with FSRS scheduler"""
    
    def __init__(
        self,
        review_repo: ReviewItemRepository,
        fsrs_service: FSRSService
    ):
        self.review_repo = review_repo
        self.fsrs = fsrs_service
    
    async def submit_review(
        self,
        review_item_id: int,
        rating: int,
        user_id: UUID
    ) -> ReviewItem:
        """
        Submit review and update schedule using FSRS.
        
        Args:
            review_item_id: Review item ID
            rating: User rating (1=Again, 2=Hard, 3=Good, 4=Easy)
            user_id: User ID for authorization
        
        Returns:
            Updated review item with next intervals
        """
        # Get review item
        review_item = await self.review_repo.get_by_id(review_item_id)
        
        if not review_item or review_item.user_id != user_id:
            raise NotFoundException("Review item not found")
        
        # Validate rating
        if rating not in [1, 2, 3, 4]:
            raise ValueError("Rating must be 1 (Again), 2 (Hard), 3 (Good), or 4 (Easy)")
        
        # Process review with FSRS
        updated_item = await self.fsrs.review_card(review_item, rating)
        
        # Save to database
        await self.review_repo.update(updated_item)
        
        return updated_item
    
    async def get_next_intervals_preview(
        self,
        review_item_id: int,
        user_id: UUID
    ) -> dict:
        """
        Preview intervals for all possible ratings.
        Shows user: "If you rate this as Good, next review in 5 days"
        
        Returns:
            {
                "again": 1,   # days
                "hard": 3,
                "good": 7,
                "easy": 14
            }
        """
        review_item = await self.review_repo.get_by_id(review_item_id)
        
        if not review_item or review_item.user_id != user_id:
            raise NotFoundException("Review item not found")
        
        # Calculate current retrievability
        if review_item.last_reviewed_at:
            elapsed = (datetime.utcnow() - review_item.last_reviewed_at).days
            retrievability = self.fsrs.calculate_retention(
                review_item.stability,
                elapsed
            )
        else:
            retrievability = 1.0
        
        # Get intervals for all ratings
        intervals = self.fsrs.get_next_intervals(
            stability=review_item.stability or 0.1,
            difficulty=review_item.difficulty or 5,
            retrievability=retrievability
        )
        
        return intervals
```

---

## Migration Strategy

### Phase 1: Add FSRS Support (Backward Compatible)

1. Add new columns to `review_items` (keep SM-2 columns)
2. Create `fsrs_parameters` table
3. Implement FSRS service
4. Add feature flag: `USE_FSRS = False`

### Phase 2: Dual Mode (A/B Test)

1. New users → FSRS by default
2. Existing users → keep SM-2, offer opt-in
3. Collect metrics: accuracy, user satisfaction

### Phase 3: Full Migration

1. Migrate existing SM-2 data → FSRS
2. Remove SM-2 columns
3. Set `USE_FSRS = True` globally

### Data Migration Script

```python
# backend/scripts/migrate_sm2_to_fsrs.py

async def migrate_review_items():
    """Convert SM-2 review items to FSRS"""
    
    items = await db.query(ReviewItem).filter(
        ReviewItem.easiness_factor.isnot(None)
    ).all()
    
    fsrs = FSRSService()
    
    for item in items:
        # Estimate FSRS parameters from SM-2
        # Stability ≈ interval_days
        item.stability = max(0.1, item.interval_days or 1)
        
        # Difficulty ≈ inverse of easiness_factor
        # SM-2: EF 1.3 (hard) - 2.5 (easy)
        # FSRS: D 1 (easy) - 10 (hard)
        ef = item.easiness_factor or 2.5
        item.difficulty = max(1, min(10, 11 - ef * 3))
        
        # Clear SM-2 fields
        item.easiness_factor = None
        item.repetitions = None
        
        # Set state
        if item.interval_days >= 21:
            item.state = "review"
        else:
            item.state = "learning"
    
    await db.commit()
```

---

## Benefits for ExamAI

1. **Better Retention**: 12% more accurate predictions → less wasted review time
2. **Personalization**: Adapts to each student's memory strength
3. **Modern Standard**: Same algorithm as Anki (50M+ users)
4. **Competitive Advantage**: Most exam prep apps still use SM-2
5. **Future-Proof**: Active development, ML-optimized

---

## Implementation Timeline

- **Week 1**: Database schema + FSRS service
- **Week 2**: Integration with StudyService + API endpoints  
- **Week 3**: Frontend UI for review buttons + interval display
- **Week 4**: Migration script + testing + deployment

---

## References

- [FSRS Algorithm Paper](https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm)
- [Anki FSRS Documentation](https://docs.ankiweb.net/deck-options.html#fsrs)
- [FSRS vs SM-2 Comparison](https://github.com/open-spaced-repetition/fsrs-vs-sm2)
