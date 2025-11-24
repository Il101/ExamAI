from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base

class ReviewLogModel(Base):
    __tablename__ = "review_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    review_item_id = Column(UUID(as_uuid=True), ForeignKey("review_items.id"), nullable=False, index=True)
    
    rating = Column(Integer, nullable=False)
    review_time = Column(DateTime, nullable=False, index=True)
    
    interval_days = Column(Integer, nullable=False)
    scheduled_days = Column(Integer, nullable=False)
    stability = Column(Float, nullable=False)
    difficulty = Column(Float, nullable=False)
    
    review_duration_ms = Column(Integer, default=0)
    
    # Relationships
    user = relationship("UserModel", back_populates="review_logs")
    review_item = relationship("ReviewItemModel", back_populates="logs")
