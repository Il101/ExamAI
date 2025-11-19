import pytest
from unittest.mock import MagicMock, AsyncMock
from app.agent.executor import TopicExecutor
from app.agent.state import AgentState, PlanStep
from app.integrations.llm.base import LLMResponse


@pytest.fixture
def mock_gemini_provider(mocker):
    """Mock Gemini provider for tests"""
    mock_llm = mocker.Mock()

    mock_response = LLMResponse(
        content="## Introduction\nThis is the content for the topic.",
        model="gemini-pro",
        tokens_input=100,
        tokens_output=200,
        cost_usd=0.005,
        finish_reason="stop",
    )

    mock_llm.generate = AsyncMock(return_value=mock_response)
    mock_llm.count_tokens.return_value = 100
    mock_llm.calculate_cost.return_value = 0.05

    return mock_llm


@pytest.mark.asyncio
class TestTopicExecutor:
    """Unit tests for TopicExecutor"""

    async def test_execute_step_success(self, mock_gemini_provider):
        """Test successful step execution"""
        # Arrange
        executor = TopicExecutor(mock_gemini_provider)
        state = AgentState(
            user_request="Teach me Calculus",
            subject="Calculus",
            exam_type="written",
            level="bachelor",
        )

        # Add a plan step
        step = PlanStep(
            id=1,
            title="Intro",
            description="Intro description",
            priority=1,
            estimated_paragraphs=3,
            dependencies=[],
        )
        state.plan = [step]
        state.current_step_index = 0

        # Act
        content = await executor.execute_step(state)

        # Assert
        assert "Introduction" in content
        mock_gemini_provider.generate.assert_called_once()
        assert state.total_tokens_used > 0
        assert state.total_cost_usd > 0

    async def test_execute_step_no_current_step(self, mock_gemini_provider):
        """Test execution with no current step"""
        # Arrange
        executor = TopicExecutor(mock_gemini_provider)
        state = AgentState(
            user_request="Teach me Calculus",
            subject="Calculus",
            exam_type="written",
            level="bachelor",
        )
        state.plan = []  # Empty plan

        # Act & Assert
        with pytest.raises(ValueError, match="No current step"):
            await executor.execute_step(state)
