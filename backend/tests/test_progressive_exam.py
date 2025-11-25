import pytest
from uuid import uuid4
from app.domain.exam import Exam
from app.services.exam_service import ExamService
from app.repositories.exam_repository import ExamRepository
from app.domain.user import User
from app.repositories.user_repository import UserRepository

@pytest.mark.asyncio
async def test_progressive_exam_flow(
    test_session,
    mocker
):
    # Mock background tasks
    mock_create_plan = mocker.patch("app.tasks.exam_tasks.create_exam_plan.delay")
    mock_generate_content = mocker.patch("app.tasks.exam_tasks.generate_exam_content.delay")
    
    # Setup dependencies
    exam_repo = ExamRepository(test_session)
    user_repo = UserRepository(test_session)
    
    # Mock services
    mock_cost_guard = mocker.Mock()
    mock_cost_guard.check_budget = mocker.AsyncMock(return_value={"allowed": True})
    mock_cost_guard.get_remaining_budget = mocker.AsyncMock(return_value=10.0)
    
    mock_llm = mocker.Mock()
    mock_llm.calculate_cost.return_value = 0.01
    
    exam_service = ExamService(
        exam_repo=exam_repo,
        cost_guard=mock_cost_guard,
        llm_provider=mock_llm
    )
    
    # Create Test User
    test_user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password"
    )
    await user_repo.create(test_user)
    
    # 1. Create Draft Exam
    exam = await exam_service.create_exam(
        user=test_user,
        title="Test Exam",
        subject="Math",
        exam_type="written",
        level="bachelor",
        original_content="This is some test content for the exam. " * 10
    )
    
    assert exam.status == "draft"
    assert exam.id is not None
    
    # 2. Create Plan
    updated_exam, task_id = await exam_service.create_plan(test_user.id, exam.id)
    
    assert updated_exam.status == "generating" # Temporarily generating while planning
    mock_create_plan.assert_called_once()
    
    # Simulate Plan Completion (manually update status since we mocked the task)
    # In real flow, the task would do this
    updated_exam.status = "planned"
    updated_exam.topic_count = 5
    await exam_service.exam_repo.update(updated_exam)
    
    # 3. Start Generation (Execute)
    # Should fail if we try to create plan again
    with pytest.raises(ValueError):
         await exam_service.create_plan(test_user.id, exam.id)
         
    # Execute
    exec_exam, exec_task_id = await exam_service.start_generation(test_user.id, exam.id)
    
    assert exec_exam.status == "generating"
    mock_generate_content.assert_called_once()
