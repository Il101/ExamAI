import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .exam import ExamModel
    from .user import UserModel


class StudySessionModel(Base):
    """SQLAlchemy StudySession model"""

    __tablename__ = "study_sessions"

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session info
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Pomodoro
    pomodoro_duration_minutes: Mapped[int] = mapped_column(
        Integer, default=25, nullable=False
    )
    break_duration_minutes: Mapped[int] = mapped_column(
        Integer, default=5, nullable=False
    )
    pomodoros_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Topics studied (array of UUIDs)
    topic_ids: Mapped[list[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, nullable=False
    )

    # Statistics
    items_reviewed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_correct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="study_sessions"
    )
    exam: Mapped["ExamModel"] = relationship(
        "ExamModel", back_populates="study_sessions"
    )

    def __repr__(self) -> str:
        return f"<StudySessionModel(id={self.id}, started_at={self.started_at})>"
