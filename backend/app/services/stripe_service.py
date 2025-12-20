import stripe
from typing import Dict, Any, Optional
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import ValidationException


class StripeService:
    """
    Service for Stripe API interactions.
    Handles checkout sessions, customer portal, and webhook events.
    """

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    def create_checkout_session(
        self,
        user_id: UUID,
        user_email: str,
        plan_type: str,
        success_url: str,
        cancel_url: str,
        billing_period: str = "monthly",
        stripe_customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create Stripe Checkout Session for subscription.

        Args:
            user_id: User UUID
            user_email: User email
            plan_type: 'pro', 'premium', or 'team'
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels
            billing_period: 'monthly' or 'yearly'
            stripe_customer_id: Existing Stripe customer ID (if any)

        Returns:
            Dict with checkout_url and session_id
        """
        # Determine price ID based on plan and billing period
        price_id = None
        
        if plan_type == "pro":
            price_id = (
                settings.STRIPE_PRICE_ID_PRO if billing_period == "monthly"
                else getattr(settings, "STRIPE_PRICE_ID_PRO_YEARLY", None)
            )
        elif plan_type == "premium":
            price_id = (
                settings.STRIPE_PRICE_ID_PREMIUM if billing_period == "monthly"
                else getattr(settings, "STRIPE_PRICE_ID_PREMIUM_YEARLY", None)
            )
        elif plan_type == "team":
            price_id = (
                getattr(settings, "STRIPE_PRICE_ID_TEAM", None) if billing_period == "monthly"
                else getattr(settings, "STRIPE_PRICE_ID_TEAM_YEARLY", None)
            )

        if not price_id:
            raise ValidationException(
                f"Stripe price ID ({billing_period}) not configured for plan: {plan_type}"
            )

        # Create or use existing customer
        if stripe_customer_id:
            customer_id = stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=user_email, metadata={"user_id": str(user_id)}
            )
            customer_id = customer.id

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": str(user_id), "plan_type": plan_type},
        )

        return {
            "checkout_url": session.url,
            "session_id": session.id,
            "customer_id": customer_id,
        }

    def create_customer_portal_session(
        self, stripe_customer_id: str, return_url: str
    ) -> str:
        """
        Create Stripe Customer Portal session.

        Args:
            stripe_customer_id: Stripe customer ID
            return_url: URL to return to after portal

        Returns:
            Portal URL
        """
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id, return_url=return_url
        )
        return session.url

    def verify_webhook_signature(
        self, payload: bytes, signature: str
    ) -> Dict[str, Any]:
        """
        Verify Stripe webhook signature and parse event.

        Args:
            payload: Raw request body
            signature: Stripe-Signature header

        Returns:
            Parsed Stripe event

        Raises:
            ValueError: If signature verification fails
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            raise ValueError(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            raise ValueError(f"Invalid signature: {str(e)}")

    def get_subscription(self, stripe_subscription_id: str) -> Dict[str, Any]:
        """
        Get subscription details from Stripe.

        Args:
            stripe_subscription_id: Stripe subscription ID

        Returns:
            Subscription data
        """
        return stripe.Subscription.retrieve(stripe_subscription_id)

    def cancel_subscription(
        self, stripe_subscription_id: str, at_period_end: bool = True
    ) -> Dict[str, Any]:
        """
        Cancel a Stripe subscription.

        Args:
            stripe_subscription_id: Stripe subscription ID
            at_period_end: If True, cancel at end of period; if False, cancel immediately

        Returns:
            Updated subscription data
        """
        if at_period_end:
            subscription = stripe.Subscription.modify(
                stripe_subscription_id, cancel_at_period_end=True
            )
        else:
            subscription = stripe.Subscription.delete(stripe_subscription_id)

        return subscription

    def reactivate_subscription(self, stripe_subscription_id: str) -> Dict[str, Any]:
        """
        Reactivate a subscription that was set to cancel at period end.

        Args:
            stripe_subscription_id: Stripe subscription ID

        Returns:
            Updated subscription data
        """
        subscription = stripe.Subscription.modify(
            stripe_subscription_id, cancel_at_period_end=False
        )
        return subscription
