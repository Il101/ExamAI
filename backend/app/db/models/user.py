from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .exam import ExamModel
    from .review import ReviewItemModel
    from .study_session import StudySessionModel
    from .subscription import SubscriptionModel
    from .topic import TopicModel


class UserModel(Base):
    """SQLAlchemy User model"""

    __tablename__ = "users"

    # Basic info
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Role & subscription
    role: Mapped[str] = mapped_column(String(50), default="student", nullable=False)
    subscription_plan: Mapped[str] = mapped_column(
        String(50), default="free", nullable=False
    )

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verification_token: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Preferences
    preferred_language: Mapped[str] = mapped_column(
        String(10), default="ru", nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    daily_study_goal_minutes: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False
    )

    # Timestamps (inherited from Base + additional)
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    exams: Mapped[list["ExamModel"]] = relationship(
        "ExamModel", back_populates="user", cascade="all, delete-orphan"
    )

    topics: Mapped[list["TopicModel"]] = relationship(
        "TopicModel", back_populates="user", cascade="all, delete-orphan"
    )

    review_items: Mapped[list["ReviewItemModel"]] = relationship(
        "ReviewItemModel", back_populates="user", cascade="all, delete-orphan"
    )

    study_sessions: Mapped[list["StudySessionModel"]] = relationship(
        "StudySessionModel", back_populates="user", cascade="all, delete-orphan"
    )

    subscriptions: Mapped[list["SubscriptionModel"]] = relationship(
        "SubscriptionModel", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserModel(id={self.id}, email={self.email})>"
