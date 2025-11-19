from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from typing import TYPE_CHECKING
import uuid
from app.db.base import Base

if TYPE_CHECKING:
    from .exam import ExamModel
    from .user import UserModel
    from .review import ReviewItemModel


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
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Metadata
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=False)
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
