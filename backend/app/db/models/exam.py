from sqlalchemy import String, Text, Integer, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import Optional, TYPE_CHECKING
import uuid
from app.db.base import Base

if TYPE_CHECKING:
    from .user import UserModel
    from .topic import TopicModel
    from .study_session import StudySessionModel


class ExamModel(Base):
    """SQLAlchemy Exam model"""
    
    __tablename__ = "exams"
    
    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Basic info
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    exam_type: Mapped[str] = mapped_column(String(50), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Content
    original_content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Metadata
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False, index=True)
    
    # AI usage tracking
    token_count_input: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    token_count_output: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    
    # Topic count
    topic_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="exams")
    
    topics: Mapped[list["TopicModel"]] = relationship(
        "TopicModel",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="TopicModel.order_index"
    )
    
    study_sessions: Mapped[list["StudySessionModel"]] = relationship(
        "StudySessionModel",
        back_populates="exam",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<ExamModel(id={self.id}, title={self.title}, status={self.status})>"
