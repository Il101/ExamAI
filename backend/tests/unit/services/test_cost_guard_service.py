import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from uuid import uuid4

from app.services.cost_guard_service import CostGuardService
from app.domain.user import User
from app.core.exceptions import BudgetExceededException


@pytest.fixture
def mock_session():
    session = AsyncMock()
    mock_result = MagicMock()
    session.execute.return_value = mock_result
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
            full_name="Test",
            subscription_plan="free",
            created_at=datetime.now()
        )
        
        # Mock today's usage: /bin/zsh.30 out of /bin/zsh.50 daily limit
        # mock_session.execute returns a MagicMock (mock_result)
        # mock_result.scalar_one_or_none() returns 0.30
        mock_session.execute.return_value.scalar_one_or_none.return_value = 0.30
        
        # Act
        estimated_cost = 0.15  # Would bring total to /bin/zsh.45
        result = await cost_guard.check_budget(user, estimated_cost)
        
        # Assert
        assert result["allowed"] is True

    @pytest.mark.asyncio
    async def test_check_budget_exceeds_limit(self, cost_guard, mock_session):
        """Test budget check when exceeding limit"""
        # Arrange
        user = User(
            id=uuid4(),
            email="test@test.com",
            full_name="Test",
            subscription_plan="free",
            created_at=datetime.now()
        )
        
        # Mock today's usage: /bin/zsh.45 out of /bin/zsh.50 daily limit
        mock_session.execute.return_value.scalar_one_or_none.return_value = 0.45
        
        # Act
        estimated_cost = 0.10  # Would bring total to /bin/zsh.55 (over limit)
        result = await cost_guard.check_budget(user, estimated_cost)
        
        # Assert
        assert result["allowed"] is False

    @pytest.mark.asyncio
    async def test_log_usage(self, cost_guard, mock_session):
        """Test logging LLM usage"""
        # Arrange
        user_id = uuid4()
        
        # Act
        await cost_guard.log_usage(
            user_id=user_id,
            operation_type="exam_generation",
            model_name="gemini-2.0-flash",
            provider="google",
            input_tokens=1000,
            output_tokens=500,
            cost_usd=0.05
        )
        
        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
