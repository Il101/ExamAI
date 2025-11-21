import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from app.services.stripe_service import StripeService
from app.core.exceptions import ValidationException
from app.core.config import settings

@pytest.fixture
def stripe_service():
    return StripeService()

def test_create_checkout_session_new_customer(stripe_service):
    user_id = uuid4()
    user_email = "test@example.com"
    plan_type = "pro"
    success_url = "http://success"
    cancel_url = "http://cancel"

    # Need to patch settings or ensure they are set
    with patch("app.services.stripe_service.settings") as mock_settings, \
         patch("app.services.stripe_service.stripe") as mock_stripe:

        mock_settings.STRIPE_PRICE_ID_PRO = "price_pro_123"

        # Mock Customer.create
        mock_customer = Mock()
        mock_customer.id = "cus_new_123"
        mock_stripe.Customer.create.return_value = mock_customer

        # Mock Session.create
        mock_session = Mock()
        mock_session.url = "http://checkout.url"
        mock_session.id = "sess_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        result = stripe_service.create_checkout_session(
            user_id, user_email, plan_type, success_url, cancel_url
        )

        assert result["checkout_url"] == "http://checkout.url"
        assert result["session_id"] == "sess_123"
        assert result["customer_id"] == "cus_new_123"

        mock_stripe.Customer.create.assert_called_once()
        mock_stripe.checkout.Session.create.assert_called_once()

def test_create_checkout_session_existing_customer(stripe_service):
    user_id = uuid4()
    user_email = "test@example.com"
    plan_type = "premium"
    success_url = "http://success"
    cancel_url = "http://cancel"
    existing_customer_id = "cus_existing_123"

    with patch("app.services.stripe_service.settings") as mock_settings, \
         patch("app.services.stripe_service.stripe") as mock_stripe:

        mock_settings.STRIPE_PRICE_ID_PREMIUM = "price_premium_123"

        # Mock Session.create
        mock_session = Mock()
        mock_session.url = "http://checkout.url"
        mock_session.id = "sess_123"
        mock_stripe.checkout.Session.create.return_value = mock_session

        result = stripe_service.create_checkout_session(
            user_id, user_email, plan_type, success_url, cancel_url,
            stripe_customer_id=existing_customer_id
        )

        assert result["customer_id"] == existing_customer_id

        mock_stripe.Customer.create.assert_not_called()
        mock_stripe.checkout.Session.create.assert_called_once()

def test_create_checkout_session_invalid_plan(stripe_service):
    with patch("app.services.stripe_service.settings") as mock_settings:
        mock_settings.STRIPE_PRICE_ID_PRO = None # Simulate missing config or similar logic if needed,
                                                 # though logic depends on settings.STRIPE_PRICE_ID_PRO

        # However, the code checks:
        # if not price_id: raise ValidationException
        # We need to make sure the lookup returns None for the given plan

        # For 'pro' plan, it looks up STRIPE_PRICE_ID_PRO.
        # For 'premium', STRIPE_PRICE_ID_PREMIUM.
        # If we pass a plan that isn't handled cleanly or if config is missing

        # Actually the code has:
        # price_id = settings.STRIPE_PRICE_ID_PRO if plan_type == "pro" else settings.STRIPE_PRICE_ID_PREMIUM
        # So if we pass "invalid", it defaults to PREMIUM's price id.
        # We need to test the case where the resulting price_id is None.

        mock_settings.STRIPE_PRICE_ID_PREMIUM = None

        with pytest.raises(ValidationException, match="Stripe price ID not configured"):
            stripe_service.create_checkout_session(
                uuid4(), "test@test.com", "invalid_plan_defaults_to_premium", "s", "c"
            )

def test_create_customer_portal_session(stripe_service):
    customer_id = "cus_123"
    return_url = "http://return"

    with patch("app.services.stripe_service.stripe") as mock_stripe:
        mock_session = Mock()
        mock_session.url = "http://portal.url"
        mock_stripe.billing_portal.Session.create.return_value = mock_session

        url = stripe_service.create_customer_portal_session(customer_id, return_url)

        assert url == "http://portal.url"
        mock_stripe.billing_portal.Session.create.assert_called_once_with(
            customer=customer_id, return_url=return_url
        )

def test_verify_webhook_signature_success(stripe_service):
    payload = b"payload"
    signature = "sig"

    with patch("app.services.stripe_service.stripe") as mock_stripe, \
         patch("app.services.stripe_service.settings") as mock_settings:

        mock_settings.STRIPE_WEBHOOK_SECRET = "secret"
        mock_event = {"id": "evt_123"}
        mock_stripe.Webhook.construct_event.return_value = mock_event

        event = stripe_service.verify_webhook_signature(payload, signature)

        assert event == mock_event
        mock_stripe.Webhook.construct_event.assert_called_once_with(
            payload, signature, "secret"
        )

def test_verify_webhook_signature_failure(stripe_service):
    payload = b"payload"
    signature = "sig"

    with patch("app.services.stripe_service.stripe") as mock_stripe, \
         patch("app.services.stripe_service.settings") as mock_settings:

        mock_settings.STRIPE_WEBHOOK_SECRET = "secret"
        mock_stripe.Webhook.construct_event.side_effect = ValueError("Bad payload")

        with pytest.raises(ValueError, match="Invalid payload"):
            stripe_service.verify_webhook_signature(payload, signature)

def test_cancel_subscription_at_period_end(stripe_service):
    sub_id = "sub_123"

    with patch("app.services.stripe_service.stripe") as mock_stripe:
        mock_sub = {"id": sub_id, "cancel_at_period_end": True}
        mock_stripe.Subscription.modify.return_value = mock_sub

        result = stripe_service.cancel_subscription(sub_id, at_period_end=True)

        assert result == mock_sub
        mock_stripe.Subscription.modify.assert_called_once_with(
            sub_id, cancel_at_period_end=True
        )

def test_cancel_subscription_immediately(stripe_service):
    sub_id = "sub_123"

    with patch("app.services.stripe_service.stripe") as mock_stripe:
        mock_sub = {"id": sub_id, "status": "canceled"}
        mock_stripe.Subscription.delete.return_value = mock_sub

        result = stripe_service.cancel_subscription(sub_id, at_period_end=False)

        assert result == mock_sub
        mock_stripe.Subscription.delete.assert_called_once_with(sub_id)

def test_reactivate_subscription(stripe_service):
    sub_id = "sub_123"

    with patch("app.services.stripe_service.stripe") as mock_stripe:
        mock_sub = {"id": sub_id, "cancel_at_period_end": False}
        mock_stripe.Subscription.modify.return_value = mock_sub

        result = stripe_service.reactivate_subscription(sub_id)

        assert result == mock_sub
        mock_stripe.Subscription.modify.assert_called_once_with(
            sub_id, cancel_at_period_end=False
        )
