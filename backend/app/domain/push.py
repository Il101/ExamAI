import uuid
from uuid import uuid4
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class PushSubscription:
    """Browser Push Subscription domain entity"""

    user_id: uuid.UUID
    endpoint: str
    p256dh: str
    auth: str
    id: uuid.UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Basic validation after initialization"""
        if not self.endpoint.startswith("https://"):
            raise ValueError("Push endpoint must be a secure URL (https)")
        if not self.p256dh or not self.auth:
            raise ValueError("Encryption keys (p256dh, auth) are required")
