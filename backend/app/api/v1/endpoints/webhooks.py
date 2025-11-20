from fastapi import APIRouter, Depends, HTTPException, status, Request
import logging

from app.dependencies import get_subscription_service, get_stripe_service
from app.services.subscription_service import SubscriptionService
from app.services.stripe_service import StripeService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    stripe_service: StripeService = Depends(get_stripe_service),
):
    """
    Handle Stripe webhook events.

    Events handled:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    - invoice.payment_succeeded
    - invoice.payment_failed
    """
    # Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header",
        )

    try:
        # Verify and parse event
        event = stripe_service.verify_webhook_signature(payload, signature)
    except ValueError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Handle the event
    event_type = event["type"]
    data = event["data"]["object"]

    logger.info(f"Received Stripe webhook: {event_type}")

    try:
        if event_type == "customer.subscription.created":
            await subscription_service.handle_subscription_created(data)
        elif event_type == "customer.subscription.updated":
            await subscription_service.handle_subscription_updated(data)
        elif event_type == "customer.subscription.deleted":
            await subscription_service.handle_subscription_deleted(data)
        elif event_type == "invoice.payment_succeeded":
            logger.info(
                f"Payment succeeded for subscription: {data.get('subscription')}"
            )
            # Could send confirmation email here
        elif event_type == "invoice.payment_failed":
            logger.warning(
                f"Payment failed for subscription: {data.get('subscription')}"
            )
            # Could send notification email here
        else:
            logger.info(f"Unhandled event type: {event_type}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error handling webhook event {event_type}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )
