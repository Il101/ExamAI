import pytest
from unittest.mock import MagicMock, AsyncMock
from app.agent.orchestrator import PlanAndExecuteAgent
from app.agent.state import AgentState, PlanStep, ExecutionStatus


@pytest.fixture
def mock_llm_provider(mocker):
    return mocker.Mock()


@pytest.mark.asyncio
class TestPlanAndExecuteAgent:
    """Unit tests for PlanAndExecuteAgent"""

    async def test_run_success(self, mock_llm_provider):
        """Test successful full execution"""
        # Arrange
        agent = PlanAndExecuteAgent(mock_llm_provider)

        # Mock components
        agent.planner = MagicMock()
        agent.executor = MagicMock()
        agent.finalizer = MagicMock()

        # Setup planner mock
        plan_steps = [
            PlanStep(
                id=1,
                title="Topic 1",
                description="Description for topic 1 that is long enough.",
                priority=1,
                estimated_paragraphs=3,
                dependencies=[],
            ),
            PlanStep(
                id=2,
                title="Topic 2",
                description="Description for topic 2 that is long enough.",
                priority=1,
                estimated_paragraphs=3,
                dependencies=[1],
            ),
        ]
        agent.planner.make_plan = AsyncMock(return_value=plan_steps)

        # Setup executor mock
        agent.executor.execute_step = AsyncMock(side_effect=["Content 1", "Content 2"])

        # Setup finalizer mock
        agent.finalizer.finalize = AsyncMock(return_value="Final Study Guide")

        # Act
        state = await agent.run(
            user_request="Teach me",
            subject="Subject",
            exam_type="written",
            level="bachelor",
        )

        # Assert
        assert state.status == ExecutionStatus.COMPLETED
        assert len(state.plan) == 2
        assert len(state.results) == 2
        assert state.final_notes == "Final Study Guide"

        agent.planner.make_plan.assert_called_once()
        assert agent.executor.execute_step.call_count == 2
        agent.finalizer.finalize.assert_called_once()

    async def test_run_failure_in_planning(self, mock_llm_provider):
        """Test failure during planning stage"""
        # Arrange
        agent = PlanAndExecuteAgent(mock_llm_provider)
        agent.planner = MagicMock()
        agent.planner.make_plan = AsyncMock(side_effect=ValueError("Planning failed"))

        # Act & Assert
        with pytest.raises(ValueError, match="Planning failed"):
            await agent.run(
                user_request="Teach me",
                subject="Subject",
                exam_type="written",
                level="bachelor",
            )
