# Stage 2: Domain Layer

**Time:** 2-3 days  
**Goal:** Implement pure domain models with business logic, SM-2 algorithm, and validation rules

## 2.1 Domain Models - Core Concepts

### Philosophy
- **Pure Python**: No framework dependencies (no SQLAlchemy, no FastAPI)
- **Rich domain models**: Business logic lives HERE, not in services
- **Immutability where possible**: Use frozen dataclasses for value objects
- **Type safety**: Full type hints, validated with mypy

---

## 2.2 User Domain Model

### Step 2.2.1: User Entity
```python
# backend/app/domain/user.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
from uuid import UUID, uuid4
import re


UserRole = Literal["student", "teacher", "admin"]
SubscriptionPlan = Literal["free", "pro", "premium"]


@dataclass
class User:
    """
    User domain entity.
    Contains core user logic: validation, subscription checks, preferences.
    """
    
    id: UUID = field(default_factory=uuid4)
    email: str = ""
    password_hash: str = ""
    full_name: str = ""
    role: UserRole = "student"
    subscription_plan: SubscriptionPlan = "free"
    
    is_verified: bool = False
    verification_token: Optional[str] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    # User preferences (for future personalization)
    preferred_language: str = "ru"
    timezone: str = "UTC"
    daily_study_goal_minutes: int = 60
    
    def __post_init__(self):
        """Validate user data on creation"""
        self._validate_email()
        self._validate_name()
    
    def _validate_email(self):
        """Email validation"""
        if not self.email:
            raise ValueError("Email is required")
        
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, self.email):
            raise ValueError(f"Invalid email format: {self.email}")
    
    def _validate_name(self):
        """Name validation"""
        if not self.full_name or len(self.full_name.strip()) < 2:
            raise ValueError("Full name must be at least 2 characters")
    
    # Business rules
    
    def can_create_exam(self) -> bool:
        """Check if user can create new exam based on subscription"""
        if not self.is_verified:
            return False
        
        # Free plan: basic access
        # Pro/Premium: unlimited
        return True
    
    def get_daily_token_limit(self) -> int:
        """Get daily LLM token limit based on subscription"""
        limits = {
            "free": 50_000,      # ~25 pages
            "pro": 500_000,      # ~250 pages
            "premium": 2_000_000  # ~1000 pages
        }
        return limits[self.subscription_plan]
    
    def get_max_exam_count(self) -> int:
        """Maximum concurrent exams"""
        limits = {
            "free": 3,
            "pro": 20,
            "premium": 100
        }
        return limits[self.subscription_plan]
    
    def mark_as_verified(self):
        """Verify user account"""
        self.is_verified = True
        self.verification_token = None
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
    
    def upgrade_subscription(self, plan: SubscriptionPlan):
        """Upgrade user subscription"""
        if plan == self.subscription_plan:
            raise ValueError(f"Already on {plan} plan")
        
        plan_hierarchy = {"free": 0, "pro": 1, "premium": 2}
        if plan_hierarchy[plan] < plan_hierarchy[self.subscription_plan]:
            raise ValueError("Cannot downgrade subscription through this method")
        
        self.subscription_plan = plan
```

---

## 2.3 Exam & Topic Domain Models

### Step 2.3.1: Exam Entity
```python
# backend/app/domain/exam.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Literal
from uuid import UUID, uuid4


ExamStatus = Literal["draft", "generating", "ready", "failed", "archived"]
ExamType = Literal["oral", "written", "test"]
ExamLevel = Literal["school", "bachelor", "master", "phd"]


@dataclass
class Exam:
    """
    Exam domain entity.
    Represents a study material with AI-generated content.
    """
    
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    
    # Basic info
    title: str = ""
    subject: str = ""
    exam_type: ExamType = "written"
    level: ExamLevel = "bachelor"
    
    # Content
    original_content: str = ""  # User-provided material
    ai_summary: Optional[str] = None  # Generated summary
    
    # Metadata
    status: ExamStatus = "draft"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # AI usage tracking
    token_count_input: int = 0
    token_count_output: int = 0
    generation_cost_usd: float = 0.0
    
    # Topics (will be populated by Agent)
    topic_count: int = 0
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate exam data"""
        if not self.title or len(self.title.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")
        
        if not self.subject or len(self.subject.strip()) < 2:
            raise ValueError("Subject must be at least 2 characters")
        
        if self.status == "ready" and not self.ai_summary:
            raise ValueError("Ready exam must have AI summary")
    
    # Business logic
    
    def can_generate(self) -> bool:
        """Check if exam can start generation"""
        return (
            self.status in ["draft", "failed"] and
            len(self.original_content) >= 100
        )
    
    def start_generation(self):
        """Mark exam as generating"""
        if not self.can_generate():
            raise ValueError(f"Cannot start generation: status={self.status}")
        
        self.status = "generating"
        self.updated_at = datetime.utcnow()
    
    def mark_as_ready(self, ai_summary: str, token_input: int, token_output: int, cost: float):
        """Mark exam as successfully generated"""
        if self.status != "generating":
            raise ValueError("Can only mark generating exams as ready")
        
        self.ai_summary = ai_summary
        self.token_count_input = token_input
        self.token_count_output = token_output
        self.generation_cost_usd = cost
        self.status = "ready"
        self.updated_at = datetime.utcnow()
    
    def mark_as_failed(self):
        """Mark exam generation as failed"""
        if self.status != "generating":
            raise ValueError("Can only mark generating exams as failed")
        
        self.status = "failed"
        self.updated_at = datetime.utcnow()
    
    def archive(self):
        """Archive exam"""
        if self.status == "generating":
            raise ValueError("Cannot archive exam during generation")
        
        self.status = "archived"
        self.updated_at = datetime.utcnow()
    
    def get_estimated_tokens(self) -> int:
        """Estimate tokens for generation (rough: 1 token ≈ 4 chars)"""
        return len(self.original_content) // 4
    
    def update_topic_count(self, count: int):
        """Update number of generated topics"""
        if count < 0:
            raise ValueError("Topic count cannot be negative")
        self.topic_count = count
        self.updated_at = datetime.utcnow()
```

### Step 2.3.2: Topic Entity
```python
# backend/app/domain/topic.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Literal
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
```

---

## 2.4 Spaced Repetition - SM-2 Algorithm

### Step 2.4.1: ReviewItem Entity with SM-2
```python
# backend/app/domain/review.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Literal
from uuid import UUID, uuid4


QualityRating = Literal[1, 2, 3, 4]
# 1 = Again (Forgot)
# 2 = Hard (Recalled with effort)
# 3 = Good (Recalled correctly)
# 4 = Easy (Recalled easily)


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
    
    # FSRS algorithm parameters
    stability: float = 0.0
    difficulty: float = 0.0
    elapsed_days: float = 0.0
    scheduled_days: int = 0
    reps: int = 0
    lapses: int = 0
    state: int = 0  # 0=New, 1=Learning, 2=Review, 3=Relearning
    
    # Review history
    next_review_date: datetime = field(default_factory=datetime.utcnow)
    last_reviewed_at: Optional[datetime] = None
    last_quality_rating: Optional[QualityRating] = None
    
    total_reviews: int = 0
    total_correct: int = 0
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        self._validate()
    
    def _validate(self):
        """Validate review item"""
        if not self.question or len(self.question.strip()) < 5:
            raise ValueError("Question must be at least 5 characters")
        
        if not self.answer or len(self.answer.strip()) < 2:
            raise ValueError("Answer must be at least 2 characters")
    
    # FSRS Algorithm Implementation
    # Based on: https://github.com/open-spaced-repetition/fsrs4anki/wiki/The-Algorithm
    
    def review(self, quality: QualityRating) -> datetime:
        """
        Apply FSRS algorithm to calculate next review date.
        
        Args:
            quality: User's recall quality (1-4)
        
        Returns:
            next_review_date
        """
        
        if not 1 <= quality <= 4:
            raise ValueError("Quality must be between 1 and 4")
        
        now = datetime.utcnow()
        
        if self.last_reviewed_at:
            self.elapsed_days = (now - self.last_reviewed_at).days
        else:
            self.elapsed_days = 0
            
        # Update statistics
        self.total_reviews += 1
        self.last_quality_rating = quality
        self.last_reviewed_at = now
        
        if quality >= 3:
            self.total_correct += 1
        
        # FSRS Logic (Simplified for implementation)
        # Constants
        DECAY = -0.5
        FACTOR = 19/81
        
        if self.state == 0: # New
            self.difficulty = self._init_difficulty(quality)
            self.stability = self._init_stability(quality)
            self.state = 1 # Learning
            
        elif self.state == 1 or self.state == 3: # Learning or Relearning
            self.difficulty = self._next_difficulty(self.difficulty, quality)
            self.stability = self._next_stability(self.difficulty, self.stability, quality)
            self.state = 2 # Review
            
        elif self.state == 2: # Review
            self.difficulty = self._next_difficulty(self.difficulty, quality)
            self.stability = self._next_stability(self.difficulty, self.stability, quality)
            
            if quality == 1: # Forgot
                self.lapses += 1
                self.state = 3 # Relearning
        
        self.reps += 1
        
        # Calculate next interval
        new_interval = int(round(self.stability * 9)) # Scaling factor
        self.scheduled_days = max(1, new_interval)
        
        self.next_review_date = now + timedelta(days=self.scheduled_days)
        
        return self.next_review_date
    
    def _init_stability(self, quality: int) -> float:
        return max(0.1, float(quality))

    def _init_difficulty(self, quality: int) -> float:
        return max(1.0, min(10.0, 5.0 - (quality - 3.0)))

    def _next_difficulty(self, d: float, r: int) -> float:
        next_d = d - 0.8 + 0.28 * (3.0 - r) + 0.02 * (3.0 - r) ** 2
        return max(1.0, min(10.0, next_d))

    def _next_stability(self, d: float, s: float, r: int) -> float:
        if r == 1:
            return max(0.1, s * 0.5) # Penalty for forgetting
        return s * (1 + math.exp(r) * (11 - d)) # Growth function
    
    def is_due(self) -> bool:
        """Check if review is due"""
        return datetime.utcnow() >= self.next_review_date
    
    def get_success_rate(self) -> float:
        """Get success rate (0.0 to 1.0)"""
        if self.total_reviews == 0:
            return 0.0
        return self.total_correct / self.total_reviews
    
    def reset(self):
        """Reset review progress"""
        self.reps = 0
        self.lapses = 0
        self.stability = 0.0
        self.difficulty = 0.0
        self.state = 0
        self.next_review_date = datetime.utcnow()
        self.last_reviewed_at = None
        self.last_quality_rating = None
```

---

## 2.5 Study Session

### Step 2.5.1: StudySession Entity
```python
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
```

---

## 2.6 Subscription & Billing

### Step 2.6.1: Subscription Entity
```python
# backend/app/domain/subscription.py
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Literal
from uuid import UUID, uuid4


SubscriptionStatus = Literal["active", "canceled", "past_due", "trialing"]


@dataclass
class Subscription:
    """
    User subscription domain entity.
    Manages billing cycles, plan changes, and access control.
    """
    
    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    
    plan_type: Literal["free", "pro", "premium"] = "free"
    status: SubscriptionStatus = "active"
    
    # Billing cycle
    current_period_start: datetime = field(default_factory=datetime.utcnow)
    current_period_end: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    
    # External billing IDs (Stripe)
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    
    # Cancel info
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Business logic
    
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return (
            self.status == "active" and
            datetime.utcnow() <= self.current_period_end
        )
    
    def can_access_feature(self, feature: str) -> bool:
        """Check feature access based on plan"""
        features_by_plan = {
            "free": ["basic_exams", "3_concurrent_exams"],
            "pro": ["basic_exams", "20_concurrent_exams", "advanced_analytics", "export_pdf"],
            "premium": ["basic_exams", "unlimited_exams", "advanced_analytics", "export_pdf", "priority_support"]
        }
        
        return feature in features_by_plan.get(self.plan_type, [])
    
    def upgrade(self, new_plan: Literal["pro", "premium"]):
        """Upgrade subscription"""
        plan_hierarchy = {"free": 0, "pro": 1, "premium": 2}
        
        if plan_hierarchy[new_plan] <= plan_hierarchy[self.plan_type]:
            raise ValueError("Can only upgrade to higher plan")
        
        self.plan_type = new_plan
        self.updated_at = datetime.utcnow()
    
    def cancel(self, immediate: bool = False):
        """Cancel subscription"""
        if immediate:
            self.status = "canceled"
            self.current_period_end = datetime.utcnow()
        else:
            self.cancel_at_period_end = True
        
        self.canceled_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def renew(self, duration_days: int = 30):
        """Renew subscription for next period"""
        if self.status != "active":
            raise ValueError("Can only renew active subscriptions")
        
        self.current_period_start = self.current_period_end
        self.current_period_end = self.current_period_start + timedelta(days=duration_days)
        self.updated_at = datetime.utcnow()
    
    def days_until_renewal(self) -> int:
        """Days until next billing"""
        delta = self.current_period_end - datetime.utcnow()
        return max(0, delta.days)
```

---

## 2.7 Unit Tests for Domain Layer

### Step 2.7.1: Test User Entity
```python
# backend/tests/unit/domain/test_user.py
import pytest
from datetime import datetime
from app.domain.user import User


class TestUser:
    """Unit tests for User domain entity"""
    
    def test_create_valid_user(self):
        """Test creating valid user"""
        user = User(
            email="test@example.com",
            full_name="Test User",
            password_hash="hashed_password"
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.subscription_plan == "free"
        assert user.is_verified is False
    
    def test_invalid_email_raises_error(self):
        """Test that invalid email raises ValueError"""
        with pytest.raises(ValueError, match="Invalid email format"):
            User(email="invalid-email", full_name="Test User")
    
    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError"""
        with pytest.raises(ValueError, match="at least 2 characters"):
            User(email="test@example.com", full_name="")
    
    def test_get_daily_token_limit(self):
        """Test token limits by subscription plan"""
        user = User(email="test@example.com", full_name="Test")
        
        assert user.get_daily_token_limit() == 50_000
        
        user.subscription_plan = "pro"
        assert user.get_daily_token_limit() == 500_000
        
        user.subscription_plan = "premium"
        assert user.get_daily_token_limit() == 2_000_000
    
    def test_mark_as_verified(self):
        """Test user verification"""
        user = User(
            email="test@example.com",
            full_name="Test",
            verification_token="abc123"
        )
        
        user.mark_as_verified()
        
        assert user.is_verified is True
        assert user.verification_token is None
    
    def test_upgrade_subscription(self):
        """Test subscription upgrade"""
        user = User(email="test@example.com", full_name="Test")
        
        user.upgrade_subscription("pro")
        assert user.subscription_plan == "pro"
        
        user.upgrade_subscription("premium")
        assert user.subscription_plan == "premium"
    
    def test_cannot_downgrade_subscription(self):
        """Test that downgrade raises error"""
        user = User(
            email="test@example.com",
            full_name="Test",
            subscription_plan="pro"
        )
        
        with pytest.raises(ValueError, match="Cannot downgrade"):
            user.upgrade_subscription("free")
```

### Step 2.7.2: Test SM-2 Algorithm
```python
# backend/tests/unit/domain/test_review.py
import pytest
from datetime import datetime, timedelta
from app.domain.review import ReviewItem


class TestReviewItemSM2:
    """Unit tests for SM-2 algorithm implementation"""
    
    def test_create_review_item(self):
        """Test creating review item"""
        item = ReviewItem(
            question="What is Python?",
            answer="A programming language"
        )
        
        assert item.repetition_number == 0
        assert item.easiness_factor == 2.5
        assert item.interval_days == 0
    
    def test_first_review_correct(self):
        """Test first review with perfect recall (quality=5)"""
        item = ReviewItem(question="Test?", answer="Answer")
        
        next_date = item.review(quality=5)
        
        assert item.repetition_number == 1
        assert item.interval_days == 1  # First repetition = 1 day
        assert item.total_reviews == 1
        assert item.total_correct == 1
        assert item.easiness_factor > 2.5  # Should increase
    
    def test_second_review_correct(self):
        """Test second review with good recall (quality=4)"""
        item = ReviewItem(question="Test?", answer="Answer")
        
        item.review(quality=5)  # First review
        item.review(quality=4)  # Second review
        
        assert item.repetition_number == 2
        assert item.interval_days == 6  # Second repetition = 6 days
    
    def test_third_review_uses_ef(self):
        """Test third review uses EF multiplier"""
        item = ReviewItem(question="Test?", answer="Answer")
        
        item.review(quality=5)  # rep=1, interval=1
        item.review(quality=5)  # rep=2, interval=6
        item.review(quality=5)  # rep=3, interval=6*EF
        
        assert item.repetition_number == 3
        assert item.interval_days > 6  # Should be 6 * EF
    
    def test_failed_review_resets_progress(self):
        """Test that quality < 3 resets progress"""
        item = ReviewItem(question="Test?", answer="Answer")
        
        item.review(quality=5)
        item.review(quality=5)
        
        assert item.repetition_number == 2
        
        # Failed review
        item.review(quality=2)
        
        assert item.repetition_number == 0  # Reset
        assert item.interval_days == 0
    
    def test_easiness_factor_decreases_on_difficulty(self):
        """Test EF decreases with low quality scores"""
        item = ReviewItem(question="Test?", answer="Answer")
        initial_ef = item.easiness_factor
        
        item.review(quality=3)  # Difficult recall
        
        assert item.easiness_factor < initial_ef
        assert item.easiness_factor >= 1.3  # Minimum EF
    
    def test_is_due(self):
        """Test is_due method"""
        item = ReviewItem(question="Test?", answer="Answer")
        
        # New item is due
        assert item.is_due() is True
        
        # After review, not due until next_review_date
        item.review(quality=5)
        item.next_review_date = datetime.utcnow() + timedelta(days=1)
        assert item.is_due() is False
    
    def test_success_rate(self):
        """Test success rate calculation"""
        item = ReviewItem(question="Test?", answer="Answer")
        
        item.review(quality=5)  # Correct
        item.review(quality=4)  # Correct
        item.review(quality=2)  # Incorrect
        
        assert item.get_success_rate() == pytest.approx(2/3)
```

---

## 2.8 Best Practices & Conventions

### Code Quality Rules

1. **Type Hints**: All functions have full type hints
2. **Validation**: Use `__post_init__` for validation
3. **Immutability**: Use frozen dataclasses for value objects
4. **Business Logic**: Domain models contain business rules, NOT services
5. **No Framework Dependencies**: Domain layer is pure Python

### Testing Strategy

- **100% coverage** for domain layer
- Test all business rules
- Test edge cases (validation, boundaries)
- Use pytest fixtures for common test data

### Next Steps

After completing domain layer:
1. Run `mypy app/domain/` to check types
2. Run `pytest tests/unit/domain/ --cov=app/domain` 
3. Ensure 100% test coverage
4. Proceed to **Stage 3: Data Layer**
