import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .user import UserModel


class SubscriptionModel(Base):
    """SQLAlchemy Subscription model"""

    __tablename__ = "subscriptions"

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Plan info
    plan_type: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)

    # Billing cycle
    current_period_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    current_period_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # External billing (Lemon Squeezy / Generic)
    external_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    external_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    customer_portal_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )

    # Webhook tracking
    last_webhook_event_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )

    # Cancel info
    cancel_at_period_end: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    canceled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    user: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="subscriptions"
    )

    def __repr__(self) -> str:
        return f"<SubscriptionModel(id={self.id}, plan={self.plan_type}, status={self.status})>"
