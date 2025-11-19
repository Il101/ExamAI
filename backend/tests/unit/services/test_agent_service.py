from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.agent.state import AgentState, PlanStep, StepResult
from app.domain.exam import Exam
from app.domain.topic import Topic
from app.domain.user import User
from app.services.agent_service import AgentService


@pytest.mark.asyncio
class TestAgentService:

    @pytest.fixture
    def mock_agent(self):
        mock = AsyncMock()
        # Mock llm attribute for cost calculation
        mock.llm = Mock()
        mock.llm.calculate_cost.return_value = 0.1
        return mock

    @pytest.fixture
    def mock_exam_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_topic_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cost_guard(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_agent, mock_exam_repo, mock_topic_repo, mock_cost_guard):
        return AgentService(
            agent=mock_agent,
            exam_repo=mock_exam_repo,
            topic_repo=mock_topic_repo,
            cost_guard=mock_cost_guard,
        )

    async def test_generate_exam_content_success(
        self, service, mock_exam_repo, mock_agent, mock_cost_guard
    ):
        # Arrange
        user = User(email="test@example.com", full_name="Test")
        exam = Exam(
            user_id=user.id,
            title="Test Exam",
            subject="Math",
            status="draft",
            original_content="Content " * 20,  # Make it long enough (>100 chars)
        )

        mock_exam_repo.get_by_user_and_id.return_value = exam
        mock_exam_repo.update.return_value = (
            exam  # Ensure update returns the exam object
        )
        mock_cost_guard.check_budget.return_value = {"allowed": True}

        # Mock agent result
        final_state = AgentState(
            user_request="Test Request",
            subject="Math",
            exam_type="written",
            level="bachelor",
        )
        final_state.final_notes = "Generated Content"
        final_state.total_tokens_used = 100
        final_state.total_cost_usd = 0.01

        # Add plan and results
        step1 = PlanStep(id=1, title="T1", description="Description 1")
        step2 = PlanStep(id=2, title="T2", description="Description 2")
        final_state.plan = [step1, step2]

        final_state.results = {
            1: StepResult(step_id=1, content="Content " * 10, success=True),
            2: StepResult(step_id=2, content="Content " * 10, success=True),
        }

        mock_agent.run.return_value = final_state

        # Act
        result = await service.generate_exam_content(user, exam.id)

        # Assert
        mock_exam_repo.get_by_user_and_id.assert_called_once_with(user.id, exam.id)
        mock_cost_guard.check_budget.assert_called_once()
        mock_agent.run.assert_called_once()
        assert result.status == "ready"
        assert result.ai_summary == "Generated Content"

    async def test_generate_exam_not_found(self, service, mock_exam_repo):
        # Arrange
        user = User(email="test@example.com", full_name="Test")
        mock_exam_repo.get_by_user_and_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Exam not found"):
            await service.generate_exam_content(user, uuid4())

    async def test_generate_exam_budget_exceeded(
        self, service, mock_exam_repo, mock_cost_guard
    ):
        # Arrange
        user = User(email="test@example.com", full_name="Test")
        exam = Exam(
            user_id=user.id,
            title="Test Exam",
            subject="Math",
            status="draft",
            original_content="Content " * 20,  # Make it long enough
        )

        mock_exam_repo.get_by_user_and_id.return_value = exam
        mock_cost_guard.check_budget.return_value = {
            "allowed": False,
            "reason": "Limit reached",
        }

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient budget"):
            await service.generate_exam_content(user, exam.id)
