# backend/app/domain/user.py
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

UserRole = Literal["student", "teacher", "admin"]
SubscriptionPlan = Literal["free", "pro", "premium", "team"]


@dataclass
class User:
    """
    User domain entity.
    Contains core user logic: validation, subscription checks, preferences.
    """

    id: UUID = field(default_factory=uuid4)
    email: str = ""
    full_name: str = ""
    role: UserRole = "student"
    subscription_plan: SubscriptionPlan = "free"

    is_verified: bool = False
    verification_token: Optional[str] = None

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None

    # User preferences (for future personalization)
    preferred_language: str = "ru"
    timezone: str = "UTC"
    daily_study_goal_minutes: int = 60
    study_days: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4, 5, 6]) # 0-6 = Mon-Sun

    # Notification Settings
    notification_exam_ready: bool = True
    notification_study_reminders: bool = True
    notification_product_updates: bool = True

    def __post_init__(self):
        """Validate user data on creation"""
        self._validate_email()
        self._validate_name()

    def _validate_email(self):
        """Email validation"""
        if not self.email:
            raise ValueError("Email is required")

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
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

        # Access is controlled by SubscriptionService/limits_config
        return True

    def get_max_exam_count(self) -> int:
        """Maximum concurrent exams"""
        from app.core.limits_config import PLAN_LIMITS
        limit = PLAN_LIMITS.get(self.subscription_plan, PLAN_LIMITS["free"]).get("max_exams")
        return limit if limit is not None else 999999

    def mark_as_verified(self):
        """Verify user account"""
        self.is_verified = True
        self.verification_token = None

    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.now(timezone.utc)

    def upgrade_subscription(self, plan: SubscriptionPlan):
        """Upgrade user subscription"""
        if plan == self.subscription_plan:
            raise ValueError(f"Already on {plan} plan")

        plan_hierarchy = {"free": 0, "pro": 1, "premium": 2, "team": 3}
        if plan_hierarchy[plan] < plan_hierarchy[self.subscription_plan]:
            raise ValueError("Cannot downgrade subscription through this method")

        self.subscription_plan = plan
