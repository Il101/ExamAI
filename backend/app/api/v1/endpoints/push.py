from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_active_user
from app.domain.user import User
from app.domain.push import PushSubscription
from app.repositories.push_subscription_repository import PushSubscriptionRepository
from app.schemas.push import PushSubscriptionCreate, PushSubscriptionResponse
from app.tasks.email_tasks import send_user_push_notification

router = APIRouter()


@router.post("/subscribe", response_model=PushSubscriptionResponse)
async def subscribe(
    payload: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Register a browser push subscription for the current user.
    """
    repo = PushSubscriptionRepository(db)
    
    # Check if subscription already exists
    existing = await repo.get_by_endpoint(payload.endpoint)
    if existing:
        return PushSubscriptionResponse(endpoint=existing.endpoint)

    subscription = PushSubscription(
        user_id=current_user.id,
        endpoint=payload.endpoint,
        p256dh=payload.p256dh,
        auth=payload.auth
    )
    
    created = await repo.create(subscription)
    return PushSubscriptionResponse(endpoint=created.endpoint)


@router.post("/unsubscribe", status_code=status.HTTP_204_NO_CONTENT)
async def unsubscribe(
    payload: PushSubscriptionCreate,  # We only need endpoint, but client sends JSON object
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Remove a browser push subscription.
    """
    repo = PushSubscriptionRepository(db)
    deleted = await repo.delete_by_endpoint(payload.endpoint)
    
    if not deleted:
        # Not found is fine for idempotent unsubscribe
        pass
    
    return None


@router.post("/test", status_code=status.HTTP_200_OK)
async def send_test_notification(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Send a test push notification to verify browser notifications are working.
    """
    repo = PushSubscriptionRepository(db)
    subscriptions = await repo.get_by_user_id(current_user.id)
    
    if not subscriptions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No browser subscriptions found. Please enable browser notifications first."
        )
    
    # Trigger async Celery task
    send_user_push_notification.delay(
        user_id=str(current_user.id),
        title="🎉 Test Notification",
        body="Great! Your browser notifications are working perfectly.",
        url="/dashboard"
    )
    
    return {"message": "Test notification sent", "subscription_count": len(subscriptions)}
