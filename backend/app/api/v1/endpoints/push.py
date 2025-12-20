from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, get_current_active_user
from app.db.models.user import UserModel
from app.domain.push import PushSubscription
from app.repositories.push_subscription_repository import PushSubscriptionRepository
from app.schemas.push import PushSubscriptionCreate, PushSubscriptionResponse

router = APIRouter()


@router.post("/subscribe", response_model=PushSubscriptionResponse)
async def subscribe(
    payload: PushSubscriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: UserModel = Depends(get_current_active_user),
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
    current_user: UserModel = Depends(get_current_active_user),
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
