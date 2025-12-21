import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from datetime import date
from app.services.course_service import CourseService
from app.domain.course import Course
from app.domain.user import User

@pytest.fixture
def course_repo():
    return MagicMock()

@pytest.fixture
def exam_repo():
    return MagicMock()

@pytest.fixture
def course_service(course_repo, exam_repo):
    return CourseService(course_repo, exam_repo)

@pytest.fixture
def sample_user():
    return User(id=uuid4(), email="test@example.com", full_name="Test User")

@pytest.fixture
def sample_course(sample_user):
    return Course(
        id=uuid4(),
        user_id=sample_user.id,
        title="Test Course",
        subject="Mathematics",
        description="A test course"
    )

@pytest.mark.asyncio
async def test_create_course(course_service, course_repo, sample_user):
    # Setup
    course_repo.create.return_value = AsyncMock()
    
    # Execute
    result = await course_service.create_course(
        user=sample_user,
        title="Test Course",
        subject="Mathematics",
        description="A test course"
    )
    
    # Verify
    assert result.title == "Test Course"
    assert result.user_id == sample_user.id
    course_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_get_course(course_service, course_repo, sample_course):
    # Setup
    course_repo.get_by_id.return_value = sample_course
    
    # Execute
    result = await course_service.get_course(sample_course.id)
    
    # Verify
    assert result == sample_course
    course_repo.get_by_id.assert_called_once_with(sample_course.id)

@pytest.mark.asyncio
async def test_list_user_courses(course_service, course_repo, sample_user, sample_course):
    # Setup
    course_repo.list_by_user.return_value = [sample_course]
    
    # Execute
    result = await course_service.list_user_courses(sample_user.id)
    
    # Verify
    assert len(result) == 1
    assert result[0] == sample_course
    course_repo.list_by_user.assert_called_once_with(sample_user.id)

@pytest.mark.asyncio
async def test_add_exam_to_course(course_service, exam_repo, sample_course):
    # Setup
    exam_id = uuid4()
    exam = MagicMock()
    exam.id = exam_id
    exam_repo.get_by_id.return_value = exam
    exam_repo.update.return_value = exam
    
    # Execute
    await course_service.add_exam_to_course(sample_course.id, exam_id)
    
    # Verify
    assert exam.course_id == sample_course.id
    exam_repo.update.assert_called_once()

@pytest.mark.asyncio
async def test_remove_exam_from_course(course_service, exam_repo):
    # Setup
    exam_id = uuid4()
    exam = MagicMock()
    exam.id = exam_id
    exam_repo.get_by_id.return_value = exam
    exam_repo.update.return_value = exam
    
    # Execute
    await course_service.remove_exam_from_course(exam_id)
    
    # Verify
    assert exam.course_id is None
    exam_repo.update.assert_called_once()
