from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class QuizResultModel(Base):
    """Quiz result tracking for MCQ quizzes"""

    __tablename__ = "quiz_results"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    topic_id = Column(PGUUID(as_uuid=True), ForeignKey("topics.id"), nullable=False)
    
    questions_total = Column(Integer, nullable=False)
    questions_correct = Column(Integer, nullable=False)
    
    completed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("UserModel", back_populates="quiz_results")
    topic = relationship("TopicModel", back_populates="quiz_results")
