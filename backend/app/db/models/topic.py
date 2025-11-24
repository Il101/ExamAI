import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .exam import ExamModel
    from .review import ReviewItemModel
    from .user import UserModel


class TopicModel(Base):
    """SQLAlchemy Topic model"""

    __tablename__ = "topics"

    # Foreign keys
    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Content
    topic_name: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    file_context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    generation_priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    estimated_study_minutes: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )

    # Relationships
    exam: Mapped["ExamModel"] = relationship("ExamModel", back_populates="topics")
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="topics")

    review_items: Mapped[list["ReviewItemModel"]] = relationship(
        "ReviewItemModel", back_populates="topic", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TopicModel(id={self.id}, topic_name={self.topic_name})>"
