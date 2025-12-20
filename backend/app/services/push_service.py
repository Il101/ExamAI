import json
import logging
from typing import Any, Dict, List, Optional

from pywebpush import webpush, WebPushException

from app.core.config import settings
from app.domain.push import PushSubscription

logger = logging.getLogger(__name__)


class PushService:
    """Service for sending browser push notifications via Web Push API"""

    def __init__(self):
        self.public_key = settings.VAPID_PUBLIC_KEY
        self.private_key = settings.VAPID_PRIVATE_KEY
        self.mailto = settings.VAPID_MAILTO

    def is_configured(self) -> bool:
        """Check if VAPID keys are configured"""
        return bool(self.public_key and self.private_key)

    async def send_notification(
        self, 
        subscription: PushSubscription, 
        title: str, 
        body: str, 
        url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send a push notification to a specific subscription.
        
        Note: This is a synchronous operation in pywebpush, 
        so it should be called from a Celery task or an async-to-sync wrapper.
        """
        if not self.is_configured():
            logger.warning("VAPID keys not configured, skipping push notification")
            return False

        try:
            payload = {
                "title": title,
                "body": body,
                "url": url or "/",
                "data": data or {}
            }

            # Generate VAPID claims
            # pywebpush will auto-fill 'aud' from endpoint if not provided
            vapid_claims = {
                "sub": self.mailto,
            }
            
            # Pass private key directly as string (base64-encoded DER or PEM file path)
            # pywebpush handles the key format internally
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh,
                        "auth": subscription.auth
                    }
                },
                data=json.dumps(payload),
                vapid_private_key=self.private_key,
                vapid_claims=vapid_claims,
            )
            return True
        except WebPushException as ex:
            logger.error(f"WebPush error: {ex}")
            # If the service reports the subscription is gone, we should handle it (delete from DB)
            # This is usually done in the calling task
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending push notification: {e}")
            return False

    async def broadcast_to_user(
        self, 
        subscriptions: List[PushSubscription], 
        title: str, 
        body: str, 
        url: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> int:
        """Send notification to all user's registered devices"""
        sent_count = 0
        for sub in subscriptions:
            success = await self.send_notification(sub, title, body, url, data)
            if success:
                sent_count += 1
        return sent_count
