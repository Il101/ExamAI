import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.domain.exam import Exam
from app.domain.user import User
from app.services.exam_service import ExamService


class TestExamServiceEncapsulation:
    @pytest.fixture
    def mock_exam_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cost_guard(self):
        return AsyncMock()

    @pytest.fixture
    def mock_llm(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_exam_repo, mock_cost_guard, mock_llm):
        return ExamService(mock_exam_repo, mock_cost_guard, mock_llm)

    @pytest.mark.asyncio
    async def test_start_generation_triggers_chain(self, service, mock_exam_repo):
        # Arrange
        user_id = uuid4()
        exam_id = uuid4()

        exam = Exam(
            id=exam_id,
            user_id=user_id,
            title="Test Exam",
            subject="Physics",
            exam_type="test",
            level="school",
            original_content="Content that is long enough to pass the validation check of 100 characters. " * 5,
            status="draft"
        )

        mock_exam_repo.get_by_user_and_id.return_value = exam
        mock_exam_repo.update.return_value = exam

        # Mock celery chain and tasks
        with patch("app.services.exam_service.chain") as mock_chain, \
             patch("app.services.exam_service.create_exam_plan") as mock_create_plan, \
             patch("app.services.exam_service.generate_exam_content") as mock_generate_content:

            mock_task_result = MagicMock()
            mock_task_result.id = "task-123"
            mock_chain.return_value.apply_async.return_value = mock_task_result

            # Act
            updated_exam, task_id = await service.start_generation(user_id, exam_id)

            # Assert
            assert task_id == "task-123"
            assert updated_exam.status == "generating"

            # Verify repo calls
            mock_exam_repo.get_by_user_and_id.assert_called_once_with(user_id, exam_id)
            mock_exam_repo.update.assert_called_once()

            # Verify celery chain was called with correct tasks
            mock_create_plan.s.assert_called_once_with(exam_id=str(exam_id), user_id=str(user_id))
            mock_generate_content.si.assert_called_once_with(exam_id=str(exam_id), user_id=str(user_id))
            mock_chain.assert_called_once_with(
                mock_create_plan.s.return_value,
                mock_generate_content.si.return_value
            )
            mock_chain.return_value.apply_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_generation_validates_status(self, service, mock_exam_repo):
        # Arrange
        user_id = uuid4()
        exam_id = uuid4()

        # Exam already generating
        exam = Exam(
            id=exam_id,
            user_id=user_id,
            title="Test Exam",
            subject="Physics",
            exam_type="test",
            level="school",
            original_content="Content that is long enough to pass the validation check of 100 characters. " * 5,
            status="generating"
        )

        mock_exam_repo.get_by_user_and_id.return_value = exam

        # Act & Assert
        # The service calls exam.can_generate() which returns False if status is "generating"
        # It then raises ValueError.
        with pytest.raises(ValueError, match="Cannot generate"):
            await service.start_generation(user_id, exam_id)
