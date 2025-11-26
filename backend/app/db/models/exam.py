import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .study_session import StudySessionModel
    from .topic import TopicModel
    from .user import UserModel


class ExamModel(Base):
    """SQLAlchemy Exam model"""

    __tablename__ = "exams"

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)

    # Content
    original_content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # V3.0 Cache fields
    cache_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    plan_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    cache_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Metadata
    status: Mapped[str] = mapped_column(
        String(50), default="draft", nullable=False, index=True
    )
    plan_ready_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # AI usage tracking
    token_count_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_cost_usd: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )

    # Topic count
    topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="exams")

    topics: Mapped[list["TopicModel"]] = relationship(
        "TopicModel",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="TopicModel.order_index",
    )

    study_sessions: Mapped[list["StudySessionModel"]] = relationship(
        "StudySessionModel", back_populates="exam", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ExamModel(id={self.id}, title={self.title}, status={self.status})>"
