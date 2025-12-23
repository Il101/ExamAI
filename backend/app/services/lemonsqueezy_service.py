import hmac
import hashlib
import json
import httpx
from typing import Dict, Any, Optional
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import ValidationException


class LemonSqueezyService:
    """
    Service for Lemon Squeezy API interactions.
    Handles checkout links, webhooks, and subscription management.
    """

    def __init__(self):
        self.api_key = settings.LEMON_SQUEEZY_API_KEY
        self.base_url = "https://api.lemonsqueezy.com/v1"
        self.headers = {
            "Accept": "application/vnd.api+json",
            "Content-Type": "application/vnd.api+json",
            "Authorization": f"Bearer {self.api_key}",
        }

    async def create_checkout_session(
        self,
        user_id: UUID,
        user_email: str,
        plan_type: str,
        success_url: str,
        cancel_url: str,
        billing_period: str = "monthly",
        external_customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a checkout URL for Lemon Squeezy.
        """
        variant_id = None
        
        if plan_type == "pro":
            variant_id = (
                settings.LEMON_SQUEEZY_VARIANT_ID_PRO if billing_period == "monthly"
                else settings.LEMON_SQUEEZY_VARIANT_ID_PRO_YEARLY
            )
        elif plan_type == "premium":
            variant_id = (
                settings.LEMON_SQUEEZY_VARIANT_ID_PREMIUM if billing_period == "monthly"
                else settings.LEMON_SQUEEZY_VARIANT_ID_PREMIUM_YEARLY
            )
        elif plan_type == "team":
            variant_id = (
                settings.LEMON_SQUEEZY_VARIANT_ID_TEAM if billing_period == "monthly"
                else settings.LEMON_SQUEEZY_VARIANT_ID_TEAM_YEARLY
            )

        if not variant_id:
            raise ValidationException(
                f"Lemon Squeezy variant ID ({billing_period}) not configured for plan: {plan_type}"
            )

        # Build payload for Lemon Squeezy Checkout API
        payload = {
            "data": {
                "type": "checkouts",
                "attributes": {
                    "checkout_data": {
                        "email": user_email,
                        "custom": {
                            "user_id": str(user_id),
                            "plan_type": plan_type
                        }
                    },
                    "product_options": {
                        "redirect_url": success_url,
                    }
                },
                "relationships": {
                    "store": {
                        "data": {
                            "type": "stores",
                            "id": settings.LEMON_SQUEEZY_STORE_ID
                        }
                    },
                    "variant": {
                        "data": {
                            "type": "variants",
                            "id": str(variant_id)
                        }
                    }
                }
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/checkouts",
                headers=self.headers,
                json=payload
            )
        
        if response.status_code != 201:
            raise ValidationException(f"Failed to create Lemon Squeezy checkout: {response.text}")

        data = response.json()
        checkout_url = data["data"]["attributes"]["url"]
        
        return {
            "checkout_url": checkout_url,
            "external_id": data["data"]["id"],
        }

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Lemon Squeezy webhook signature.
        """
        if not signature:
            return False
            
        secret = settings.LEMON_SQUEEZY_WEBHOOK_SECRET.encode("utf-8")
        digest = hmac.new(secret, payload, hashlib.sha256).hexdigest()
        
        return hmac.compare_digest(digest, signature)

    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Retrieve subscription details from Lemon Squeezy.
        """
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/subscriptions/{subscription_id}",
                headers=self.headers
            )
        
        if response.status_code != 200:
            raise ValidationException(f"Failed to fetch Lemon Squeezy subscription: {response.text}")
            
        return response.json()

    async def cancel_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Cancel a Lemon Squeezy subscription.
        """
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/subscriptions/{subscription_id}",
                headers=self.headers
            )
        
        if response.status_code != 200:
            raise ValidationException(f"Failed to cancel Lemon Squeezy subscription: {response.text}")
            
        return response.json()
