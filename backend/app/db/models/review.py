import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .topic import TopicModel
    from .user import UserModel
    from .review_log import ReviewLogModel


class ReviewItemModel(Base):
    """SQLAlchemy ReviewItem model for spaced repetition"""

    __tablename__ = "review_items"

    # Foreign keys
    topic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Question/Answer
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    # FSRS algorithm parameters
    stability: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    elapsed_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    scheduled_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    lapses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    state: Mapped[str] = mapped_column(String(20), default="new", nullable=False)

    # Review history
    next_review_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,  # Index for efficient "due today" queries
    )
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_review_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    topic: Mapped["TopicModel"] = relationship(
        "TopicModel", back_populates="review_items"
    )
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="review_items")

    logs: Mapped[list["ReviewLogModel"]] = relationship(
        "ReviewLogModel", back_populates="review_item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ReviewItemModel(id={self.id}, next_review={self.next_review_date})>"
