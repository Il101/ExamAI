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
            original_content="This is a long content string that is definitely over 100 characters to pass the validation check in the service.",
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
                original_content="This is a long content string that is definitely over 100 characters to pass the validation check in the service.",
            )

    @pytest.mark.asyncio
    async def test_start_generation_creates_chain(self, service, mock_repo, user, mocker):
        # Mocks
        exam_id = uuid4()
        user_id = user.id
        mock_exam = Mock()
        mock_exam.can_generate.return_value = True
        mock_repo.get_by_user_and_id.return_value = mock_exam

        # Mock Celery chain and tasks
        mock_chain = mocker.patch("app.services.exam_service.chain")
        mock_create_plan = mocker.patch("app.services.exam_service.create_exam_plan")
        mock_generate_content = mocker.patch(
            "app.services.exam_service.generate_exam_content"
        )
        mock_task = Mock()
        mock_chain.return_value.apply_async.return_value = mock_task

        # Execute
        _, task_id = await service.start_generation(user_id, exam_id)

        # Verify
        mock_repo.get_by_user_and_id.assert_called_with(user_id, exam_id)
        mock_exam.start_generation.assert_called_once()
        mock_repo.update.assert_called_with(mock_exam)

        # Verify chain was called with correct tasks
        mock_create_plan.s.assert_called_with(exam_id=str(exam_id), user_id=str(user_id))
        mock_generate_content.si.assert_called_with(
            exam_id=str(exam_id), user_id=str(user_id)
        )
        mock_chain.assert_called_once_with(
            mock_create_plan.s.return_value, mock_generate_content.si.return_value
        )

        # Verify that the chain was executed
        mock_chain.return_value.apply_async.assert_called_once()
        assert task_id == mock_task.id

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
                original_content="This is a long content string that is definitely over 100 characters to pass the validation check in the service.",
            )
