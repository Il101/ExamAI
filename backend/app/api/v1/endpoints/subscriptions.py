from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.dependencies import get_current_active_user, get_subscription_service
from app.domain.user import User
from app.services.subscription_service import SubscriptionService
from app.schemas.subscription import (
    PlanResponse,
    SubscriptionResponse,
    CreateCheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    UsageResponse,
)
from app.core.config import settings

router = APIRouter()


@router.get("/plans", response_model=List[PlanResponse])
async def get_plans(
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get available subscription plans"""
    plans = subscription_service.get_available_plans()
    return plans


@router.get("/current", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_active_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get user's current subscription"""
    subscription = await subscription_service.get_user_subscription(current_user.id)
    return SubscriptionResponse.from_orm(subscription)


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CreateCheckoutRequest,
    current_user: User = Depends(get_current_active_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Create Lemon Squeezy Checkout session"""
    try:
        result = await subscription_service.create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            plan_type=request.plan_id,
            success_url=request.success_url,
            cancel_url=request.cancel_url,
            billing_period=request.billing_period,
        )
        return CheckoutResponse(checkout_url=result["checkout_url"])
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/cancel", response_model=SubscriptionResponse)
async def cancel_subscription(
    current_user: User = Depends(get_current_active_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Cancel subscription (at period end)"""
    try:
        subscription = await subscription_service.cancel_subscription(current_user.id)
        return SubscriptionResponse.from_orm(subscription)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reactivate", response_model=SubscriptionResponse)
async def reactivate_subscription(
    current_user: User = Depends(get_current_active_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Reactivate canceled subscription (stub)"""
    # Lemon Squeezy reactivation is usually handled via their portal
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Reactivation is managed via the billing portal.",
    )


@router.post("/portal", response_model=PortalResponse)
async def get_portal(
    current_user: User = Depends(get_current_active_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get Lemon Squeezy Customer Portal link"""
    try:
        subscription = await subscription_service.get_user_subscription(current_user.id)

        if not subscription.external_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No billing record found. Purchase a plan first.",
            )

        # Lemon Squeezy customer portal (General link for the store)
        # Note: Lemon Squeezy often handles this via "My Orders" or subscription.attributes.urls.customer_portal
        portal_url = f"https://{settings.LEMON_SQUEEZY_STORE_ID}.lemonsqueezy.com/billing"
        
        return PortalResponse(portal_url=portal_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/usage", response_model=UsageResponse)
async def get_usage_metrics(
    current_user: User = Depends(get_current_active_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get summarized usage metrics for the current user's plan"""
    return await subscription_service.get_usage_metrics(current_user.id)
