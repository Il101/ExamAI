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
    """Create Stripe Checkout session"""
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
    """Reactivate canceled subscription"""
    try:
        subscription = await subscription_service.reactivate_subscription(
            current_user.id
        )
        return SubscriptionResponse.from_orm(subscription)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/portal", response_model=PortalResponse)
async def get_portal(
    current_user: User = Depends(get_current_active_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """Get Stripe Customer Portal link"""
    try:
        subscription = await subscription_service.get_user_subscription(current_user.id)

        if not subscription.stripe_customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe customer found",
            )

        return_url = f"{settings.FRONTEND_URL}/subscription"
        portal_url = subscription_service.get_customer_portal_url(
            subscription.stripe_customer_id, return_url
        )

        return PortalResponse(portal_url=portal_url)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
