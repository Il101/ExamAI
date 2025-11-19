from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from app.domain.user import User
from app.services.exam_service import ExamService


class TestExamService:

    @pytest.fixture
    def mock_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cost_guard(self):
        return AsyncMock()

    @pytest.fixture
    def mock_llm(self):
        mock = Mock()
        mock.calculate_cost.return_value = 0.01
        return mock

    @pytest.fixture
    def service(self, mock_repo, mock_cost_guard, mock_llm):
        return ExamService(mock_repo, mock_cost_guard, mock_llm)

    @pytest.fixture
    def user(self):
        return User(
            id=uuid4(),
            email="test@example.com",
            full_name="Test User",
            subscription_plan="free",
        )

    @pytest.mark.asyncio
    async def test_create_exam_success(self, service, mock_repo, mock_cost_guard, user):
        # Setup mocks
        mock_repo.count_by_user.return_value = 0
        mock_cost_guard.check_budget.return_value = {"allowed": True}
        mock_repo.create.side_effect = lambda x: x  # Return the exam passed to it

        # Execute
        exam = await service.create_exam(
            user=user,
            title="Physics 101",
            subject="Physics",
            exam_type="written",
            level="bachelor",
            original_content="Content...",
        )

        # Verify
        assert exam.title == "Physics 101"
        assert exam.status == "draft"
        mock_repo.create.assert_called_once()
        mock_cost_guard.check_budget.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_exam_limit_reached(self, service, mock_repo, user):
        # Setup mocks
        # Free plan limit is usually low (e.g. 3)
        mock_repo.count_by_user.return_value = 5

        # Execute & Verify
        with pytest.raises(ValueError, match="Exam limit reached"):
            await service.create_exam(
                user=user,
                title="Physics 101",
                subject="Physics",
                exam_type="written",
                level="bachelor",
                original_content="Content...",
            )

    @pytest.mark.asyncio
    async def test_create_exam_insufficient_budget(
        self, service, mock_repo, mock_cost_guard, user
    ):
        # Setup mocks
        mock_repo.count_by_user.return_value = 0
        mock_cost_guard.check_budget.return_value = {"allowed": False}
        mock_cost_guard.get_remaining_budget.return_value = 0.05

        # Execute & Verify
        with pytest.raises(ValueError, match="Insufficient budget"):
            await service.create_exam(
                user=user,
                title="Physics 101",
                subject="Physics",
                exam_type="written",
                level="bachelor",
                original_content="Content...",
            )
