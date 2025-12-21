import uuid
from datetime import datetime, date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .exam import ExamModel
    from .user import UserModel


class CourseModel(Base):
    """SQLAlchemy Course model (folder for exams)"""

    __tablename__ = "courses"

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
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Semester info
    semester_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    semester_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Exam scheduling
    exam_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="courses")
    exams: Mapped[list["ExamModel"]] = relationship(
        "ExamModel",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<CourseModel(id={self.id}, title={self.title}, subject={self.subject})>"
