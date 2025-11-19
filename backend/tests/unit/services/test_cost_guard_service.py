# backend/tests/unit/services/test_cost_guard_service.py
from datetime import datetime
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.domain.user import User
from app.services.cost_guard_service import CostGuardService


@pytest.fixture
def mock_session():
    session = AsyncMock()
    # Ensure the result of execute is a standard Mock (synchronous), not AsyncMock
    result_mock = Mock()
    session.execute.return_value = result_mock
    return session


@pytest.fixture
def cost_guard(mock_session):
    return CostGuardService(session=mock_session)


class TestCostGuardService:
    """Unit tests for CostGuardService"""

    @pytest.mark.asyncio
    async def test_check_budget_within_limit(self, cost_guard, mock_session):
        """Test budget check when within limit"""
        # Arrange
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test User",
            subscription_plan="free",
            created_at=datetime.now(),
        )

        # Mock today's usage: $0.30 out of $0.50 daily limit
        # Access the return value we set in the fixture
        mock_session.execute.return_value.scalar_one_or_none.return_value = 0.30

        # Act
        # Remaining: 0.20. Safety buffer 95% -> 0.19 usable.
        # Cost 0.15 <= 0.19 -> Allowed
        result = await cost_guard.check_budget(user, estimated_cost=0.15)

        # Assert
        assert result["allowed"] is True
        assert result["buffer_applied"] is True

    @pytest.mark.asyncio
    async def test_check_budget_exceeds_buffer(self, cost_guard, mock_session):
        """Test budget check when exceeding safety buffer but within absolute limit"""
        # Arrange
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test User",
            subscription_plan="free",
            created_at=datetime.now(),
        )

        # Mock today's usage: $0.30 out of $0.50 daily limit
        mock_session.execute.return_value.scalar_one_or_none.return_value = 0.30

        # Act
        # Remaining: 0.20. Safety buffer 95% -> 0.19 usable.
        # Cost 0.195 > 0.19 -> Not Allowed (due to buffer)
        result = await cost_guard.check_budget(user, estimated_cost=0.195)

        # Assert
        assert result["allowed"] is False
        assert "Insufficient budget" in result["reason"]

    @pytest.mark.asyncio
    async def test_check_budget_no_buffer(self, cost_guard, mock_session):
        """Test budget check without safety buffer"""
        # Arrange
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test User",
            subscription_plan="free",
            created_at=datetime.now(),
        )

        # Mock today's usage: $0.30 out of $0.50 daily limit
        mock_session.execute.return_value.scalar_one_or_none.return_value = 0.30

        # Act
        # Remaining: 0.20. No buffer -> 0.20 usable.
        # Cost 0.195 <= 0.20 -> Allowed
        result = await cost_guard.check_budget(
            user, estimated_cost=0.195, apply_buffer=False
        )

        # Assert
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_handle_actual_cost_overage_free_tier(self, cost_guard):
        """Test overage handling for free tier (strict)"""
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test User",
            subscription_plan="free",
        )

        # Estimate 0.10, Actual 0.12 -> 20% overage
        # Free tier max overage is 0%
        result = await cost_guard.handle_actual_cost_overage(user, 0.10, 0.12)

        assert result["action"] == "block"
        assert result["overage"] == pytest.approx(0.02)

    @pytest.mark.asyncio
    async def test_handle_actual_cost_overage_premium_tier(self, cost_guard):
        """Test overage handling for premium tier (lenient)"""
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test User",
            subscription_plan="premium",
        )

        # Estimate 0.10, Actual 0.105 -> 5% overage
        # Premium tier max overage is 10%
        result = await cost_guard.handle_actual_cost_overage(user, 0.10, 0.105)

        assert result["action"] == "allow"

    @pytest.mark.asyncio
    async def test_log_usage(self, cost_guard, mock_session):
        """Test logging usage"""
        await cost_guard.log_usage(
            user_id=uuid4(),
            model_name="gpt-4",
            provider="openai",
            operation_type="chat",
            input_tokens=10,
            output_tokens=20,
            cost_usd=0.01,
        )

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
