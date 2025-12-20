import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from .user import UserModel


class PushSubscriptionModel(Base):
    """SQLAlchemy model for storing browser push subscriptions"""

    __tablename__ = "push_subscriptions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="push_subscriptions")

    def __repr__(self) -> str:
        return f"<PushSubscriptionModel(id={self.id}, user_id={self.user_id}, endpoint={self.endpoint[:30]}...)>"
