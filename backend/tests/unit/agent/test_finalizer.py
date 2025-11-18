import pytest
from unittest.mock import MagicMock, AsyncMock
from app.agent.finalizer import NoteFinalizer
from app.agent.state import AgentState, PlanStep, StepResult
from app.integrations.llm.base import LLMResponse

@pytest.fixture
def mock_gemini_provider(mocker):
    """Mock Gemini provider for tests"""
    mock_llm = mocker.Mock()
    
    mock_response = LLMResponse(
        content="# Final Study Guide\n\n## Topic 1\nContent 1",
        model="gemini-pro",
        tokens_input=100,
        tokens_output=200,
        cost_usd=0.005,
        finish_reason="stop"
    )
    
    mock_llm.generate = AsyncMock(return_value=mock_response)
    mock_llm.count_tokens.return_value = 100
    mock_llm.calculate_cost.return_value = 0.05
    
    return mock_llm

@pytest.mark.asyncio
class TestNoteFinalizer:
    """Unit tests for NoteFinalizer"""

    async def test_finalize_success(self, mock_gemini_provider):
        """Test successful finalization"""
        # Arrange
        finalizer = NoteFinalizer(mock_gemini_provider)
        state = AgentState(
            user_request="Teach me Calculus",
            subject="Calculus",
            exam_type="written",
            level="bachelor"
        )
        
        # Add plan and results
        step = PlanStep(id=1, title="Topic 1", description="Description for topic 1 that is long enough.", priority=1, estimated_paragraphs=3, dependencies=[])
        state.plan = [step]
        state.results[1] = StepResult(step_id=1, content="Content 1", success=True)
        
        # Act
        final_notes = await finalizer.finalize(state)
        
        # Assert
        assert "# Final Study Guide" in final_notes
        mock_gemini_provider.generate.assert_called_once()
        assert state.total_tokens_used > 0

    async def test_finalize_no_results(self, mock_gemini_provider):
        """Test finalization with no results"""
        # Arrange
        finalizer = NoteFinalizer(mock_gemini_provider)
        state = AgentState(
            user_request="Teach me Calculus",
            subject="Calculus",
            exam_type="written",
            level="bachelor"
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="No results to finalize"):
            await finalizer.finalize(state)
