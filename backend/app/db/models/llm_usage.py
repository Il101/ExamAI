from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from typing import Optional, Any
from datetime import datetime
from app.db.base import Base
import uuid


class LLMUsageLogModel(Base):
    """SQLAlchemy LLM Usage Log model"""

    __tablename__ = "llm_usage_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    study_material_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )  # Assuming study_materials table exists but not strictly enforcing FK here to avoid circular deps if not needed, or I should check if StudyMaterialModel exists.

    # LLM details
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Token usage
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    # total_tokens is generated, so we might not map it or map it as read-only if needed.
    # For simplicity in python, we can just calculate it or ignore the generated column if we don't query it often.
    # But if we want to map it:
    # total_tokens: Mapped[int] = mapped_column(Integer, Computed("input_tokens + output_tokens"), nullable=True)

    # Cost tracking
    cost_usd: Mapped[float] = mapped_column(Float, nullable=False)

    # Performance metrics
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cache_hit: Mapped[bool] = mapped_column(Boolean, default=False)

    # Request context
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, index=True
    )
    request_metadata: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB, default={}
    )

    # Error tracking
    error_occurred: Mapped[bool] = mapped_column(Boolean, default=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user = relationship("UserModel", backref="llm_logs")
