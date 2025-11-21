import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from app.services.subscription_service import SubscriptionService
from app.domain.subscription import Subscription

@pytest.fixture
def mock_repo():
    return AsyncMock()

@pytest.fixture
def mock_stripe_service():
    return Mock()

@pytest.fixture
def subscription_service(mock_repo, mock_stripe_service):
    return SubscriptionService(mock_repo, mock_stripe_service)

@pytest.mark.asyncio
async def test_get_available_plans(subscription_service):
    plans = subscription_service.get_available_plans()
    assert len(plans) == 3
    assert plans[0]["id"] == "free"
    assert plans[1]["id"] == "pro"
    assert plans[2]["id"] == "premium"

@pytest.mark.asyncio
async def test_get_user_subscription_existing(subscription_service, mock_repo):
    user_id = uuid4()
    existing_sub = Subscription(
        user_id=user_id,
        plan_type="pro",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=30)
    )
    mock_repo.get_by_user_id.return_value = existing_sub

    sub = await subscription_service.get_user_subscription(user_id)

    assert sub == existing_sub
    mock_repo.get_by_user_id.assert_called_once_with(user_id)
    mock_repo.create.assert_not_called()

@pytest.mark.asyncio
async def test_get_user_subscription_create_default(subscription_service, mock_repo):
    user_id = uuid4()
    mock_repo.get_by_user_id.return_value = None

    # Mock the create return value to be the same object passed to it (or similar)
    async def side_effect(sub):
        return sub
    mock_repo.create.side_effect = side_effect

    sub = await subscription_service.get_user_subscription(user_id)

    assert sub.user_id == user_id
    assert sub.plan_type == "free"
    assert sub.status == "active"
    mock_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_create_checkout_session_new_customer(subscription_service, mock_repo, mock_stripe_service):
    user_id = uuid4()
    email = "test@example.com"

    # Existing subscription has no customer_id
    existing_sub = Subscription(
        user_id=user_id,
        plan_type="free",
        stripe_customer_id=None,
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )
    mock_repo.get_by_user_id.return_value = existing_sub

    mock_stripe_service.create_checkout_session.return_value = {
        "checkout_url": "http://checkout",
        "customer_id": "cus_123"
    }

    result = await subscription_service.create_checkout_session(
        user_id, email, "pro", "http://success", "http://cancel"
    )

    assert result["checkout_url"] == "http://checkout"
    assert existing_sub.stripe_customer_id == "cus_123"
    mock_repo.update.assert_called_once_with(existing_sub)

@pytest.mark.asyncio
async def test_handle_subscription_created(subscription_service, mock_repo):
    user_id = uuid4()
    stripe_sub = {
        "id": "sub_123",
        "customer": "cus_123",
        "metadata": {"user_id": str(user_id), "plan_type": "pro"},
        "current_period_start": 1000000000,
        "current_period_end": 1000003600,
        "status": "active"
    }

    existing_sub = Subscription(
        user_id=user_id,
        plan_type="free",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )
    mock_repo.get_by_user_id.return_value = existing_sub

    await subscription_service.handle_subscription_created(stripe_sub)

    assert existing_sub.plan_type == "pro"
    assert existing_sub.stripe_subscription_id == "sub_123"
    mock_repo.update.assert_called_once_with(existing_sub)

@pytest.mark.asyncio
async def test_handle_subscription_updated(subscription_service, mock_repo):
    stripe_sub = {
        "id": "sub_123",
        "status": "past_due",
        "current_period_end": 1000003600,
        "cancel_at_period_end": True
    }

    existing_sub = Subscription(
        user_id=uuid4(),
        plan_type="pro",
        stripe_subscription_id="sub_123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )
    mock_repo.get_by_stripe_subscription_id.return_value = existing_sub

    await subscription_service.handle_subscription_updated(stripe_sub)

    assert existing_sub.status == "past_due"
    assert existing_sub.cancel_at_period_end is True
    mock_repo.update.assert_called_once_with(existing_sub)

@pytest.mark.asyncio
async def test_handle_subscription_deleted(subscription_service, mock_repo):
    stripe_sub = {"id": "sub_123"}

    existing_sub = Subscription(
        user_id=uuid4(),
        plan_type="pro",
        stripe_subscription_id="sub_123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )
    mock_repo.get_by_stripe_subscription_id.return_value = existing_sub

    await subscription_service.handle_subscription_deleted(stripe_sub)

    assert existing_sub.plan_type == "free"
    assert existing_sub.status == "canceled"
    assert existing_sub.stripe_subscription_id is None
    mock_repo.update.assert_called_once_with(existing_sub)

@pytest.mark.asyncio
async def test_cancel_subscription(subscription_service, mock_repo, mock_stripe_service):
    user_id = uuid4()
    existing_sub = Subscription(
        user_id=user_id,
        plan_type="pro",
        stripe_subscription_id="sub_123",
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )
    mock_repo.get_by_user_id.return_value = existing_sub

    await subscription_service.cancel_subscription(user_id)

    mock_stripe_service.cancel_subscription.assert_called_once_with("sub_123", at_period_end=True)
    assert existing_sub.cancel_at_period_end is True
    mock_repo.update.assert_called_once_with(existing_sub)

@pytest.mark.asyncio
async def test_reactivate_subscription(subscription_service, mock_repo, mock_stripe_service):
    user_id = uuid4()
    existing_sub = Subscription(
        user_id=user_id,
        plan_type="pro",
        stripe_subscription_id="sub_123",
        status="active",
        cancel_at_period_end=True,
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )
    mock_repo.get_by_user_id.return_value = existing_sub

    await subscription_service.reactivate_subscription(user_id)

    mock_stripe_service.reactivate_subscription.assert_called_once_with("sub_123")
    assert existing_sub.cancel_at_period_end is False
    mock_repo.update.assert_called_once_with(existing_sub)
