from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PlanResponse(BaseModel):
    """Subscription plan details"""

    id: str
    name: str
    description: Optional[str] = None
    price: Dict[str, Any]
    limits: Optional[Dict[str, Any]] = None
    features: Dict[str, Any]
    lemonsqueezy_variant_id_monthly: Optional[str] = None
    lemonsqueezy_variant_id_yearly: Optional[str] = None
    popular: Optional[bool] = False


class SubscriptionResponse(BaseModel):
    """User subscription response"""

    id: UUID
    user_id: UUID
    plan_type: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    external_subscription_id: Optional[str] = None
    external_customer_id: Optional[str] = None
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateCheckoutRequest(BaseModel):
    """Create checkout session request"""

    plan_id: str  # 'pro', 'premium', or 'team'
    billing_period: Optional[str] = "monthly"
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Checkout session response"""

    checkout_url: str


class PortalResponse(BaseModel):
    """Customer portal response"""

    portal_url: str
