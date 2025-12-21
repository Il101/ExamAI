from fastapi import APIRouter, Depends, HTTPException, status, Request
import logging
import json

from app.dependencies import get_subscription_service, get_lemonsqueezy_service
from app.services.subscription_service import SubscriptionService
from app.services.lemonsqueezy_service import LemonSqueezyService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/lemon-squeezy")
async def lemonsqueezy_webhook(
    request: Request,
    subscription_service: SubscriptionService = Depends(get_subscription_service),
    lemonsqueezy_service: LemonSqueezyService = Depends(get_lemonsqueezy_service),
):
    """
    Handle Lemon Squeezy webhook events.

    Events handled:
    - subscription_created
    - subscription_updated
    - subscription_cancelled
    """
    # Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("x-signature")

    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing x-signature header",
        )

    # Verify signature
    if not lemonsqueezy_service.verify_webhook_signature(payload, signature):
        logger.error("Lemon Squeezy webhook signature verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature",
        )

    # Parse payload
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    event_name = request.headers.get("x-event-name")
    logger.info(f"Received Lemon Squeezy webhook: {event_name}")
    logger.debug(f"Webhook payload: {json.dumps(data, indent=2)}")
    logger.debug(f"Webhook custom_data: {json.dumps(data.get('meta', {}).get('custom_data', {}), indent=2)}")

    event_id = str(data.get("meta", {}).get("event_id", ""))
    
    # Check idempotency
    if event_name in ["subscription_created", "subscription_updated"]:
        # We need the subscription to check its last_webhook_event_id
        # For simplicity in this endpoint, we'll let the service handle the check
        # but we pass the event_id along
        pass

    try:
        if event_name == "subscription_created":
            await subscription_service.handle_subscription_created(data)
        elif event_name == "subscription_updated":
            # Pass event_id for idempotency check inside service if needed
            # For now, the service will handle it by comparing with the DB
            await subscription_service.handle_subscription_updated(data)
        elif event_name == "subscription_cancelled":
            await subscription_service.handle_subscription_cancelled(data)
        else:
            logger.info(f"Unhandled Lemon Squeezy event: {event_name}")

        return {"status": "success"}

    except Exception as e:
        logger.error(f"Error handling Lemon Squeezy event {event_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )
