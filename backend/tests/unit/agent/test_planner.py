import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from app.agent.planner import CoursePlanner
from app.agent.state import AgentState
from app.integrations.llm.base import LLMResponse


@pytest.fixture
def mock_gemini_provider(mocker):
    """Mock Gemini provider for tests"""
    mock_llm = mocker.Mock()

    # Create a valid plan list with 5 topics (minimum required)
    plan_data = [
        {
            "id": 1,
            "title": "Topic 1",
            "description": "Description for topic 1 that is long enough.",
            "priority": 1,
            "estimated_paragraphs": 5,
            "dependencies": [],
        },
        {
            "id": 2,
            "title": "Topic 2",
            "description": "Description for topic 2 that is long enough.",
            "priority": 1,
            "estimated_paragraphs": 5,
            "dependencies": [1],
        },
        {
            "id": 3,
            "title": "Topic 3",
            "description": "Description for topic 3 that is long enough.",
            "priority": 2,
            "estimated_paragraphs": 5,
            "dependencies": [2],
        },
        {
            "id": 4,
            "title": "Topic 4",
            "description": "Description for topic 4 that is long enough.",
            "priority": 2,
            "estimated_paragraphs": 5,
            "dependencies": [3],
        },
        {
            "id": 5,
            "title": "Topic 5",
            "description": "Description for topic 5 that is long enough.",
            "priority": 3,
            "estimated_paragraphs": 5,
            "dependencies": [4],
        },
    ]

    # Create LLMResponse object
    mock_response = LLMResponse(
        content=json.dumps(plan_data),
        model="gemini-pro",
        tokens_input=100,
        tokens_output=200,
        cost_usd=0.005,
        finish_reason="stop",
    )

    # Mock generate to be async and return the LLMResponse
    mock_llm.generate = AsyncMock(return_value=mock_response)

    mock_llm.count_tokens.return_value = 100
    mock_llm.calculate_cost.return_value = 0.05

    return mock_llm


@pytest.mark.asyncio
class TestCoursePlanner:
    """Unit tests for CoursePlanner"""

    async def test_make_plan_success(self, mock_gemini_provider):
        """Test successful plan generation"""
        # Arrange
        planner = CoursePlanner(mock_gemini_provider)
        state = AgentState(
            user_request="Teach me Calculus",
            subject="Calculus",
            exam_type="written",
            level="bachelor",
        )

        # Act
        plan = await planner.make_plan(state)

        # Assert
        assert len(plan) == 5
        assert plan[0].title == "Topic 1"
        assert plan[4].title == "Topic 5"

        mock_gemini_provider.generate.assert_called_once()

    async def test_make_plan_failure(self, mock_gemini_provider):
        """Test plan generation failure"""
        # Arrange
        mock_gemini_provider.generate.side_effect = Exception("LLM Error")
        planner = CoursePlanner(mock_gemini_provider)
        state = AgentState(
            user_request="Teach me Calculus",
            subject="Calculus",
            exam_type="written",
            level="bachelor",
        )

        # Act & Assert
        # Expect the actual exception raised by the mock
        with pytest.raises(Exception, match="LLM Error"):
            await planner.make_plan(state)
