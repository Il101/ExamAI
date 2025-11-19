import pytest
from uuid import uuid4
from app.repositories.exam_repository import ExamRepository
from app.repositories.user_repository import UserRepository
from app.domain.exam import Exam, ExamStatus
from app.domain.user import User

@pytest.mark.integration
@pytest.mark.asyncio
class TestExamRepository:
    
    async def create_user(self, session):
        user_repo = UserRepository(session)
        user = User(
            email=f"test_{uuid4()}@example.com",
            full_name="Test User"
        )
        return await user_repo.create(user)

    async def test_create_and_get(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        repo = ExamRepository(test_session)
        exam = Exam(
            user_id=user.id,
            title="Test Exam",
            subject="Math"
        )
        
        # Act
        created = await repo.create(exam)
        retrieved = await repo.get_by_id(created.id)
        
        # Assert
        assert created.id is not None
        assert created.title == "Test Exam"
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == user.id

    async def test_list_by_user(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        repo = ExamRepository(test_session)
        
        exam1 = Exam(user_id=user.id, title="Exam 1", status="draft", subject="Math")
        exam2 = Exam(user_id=user.id, title="Exam 2", status="ready", subject="Physics", ai_summary="Summary")
        
        # Create another user and exam
        other_user = await self.create_user(test_session)
        exam3 = Exam(user_id=other_user.id, title="Other User Exam", subject="History")
        
        await repo.create(exam1)
        await repo.create(exam2)
        await repo.create(exam3)
        
        # Act
        all_exams = await repo.list_by_user(user.id)
        ready_exams = await repo.list_by_user(user.id, status="ready")
        
        # Assert
        assert len(all_exams) == 2
        assert len(ready_exams) == 1
        assert ready_exams[0].title == "Exam 2"

    async def test_count_by_user(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        repo = ExamRepository(test_session)
        
        await repo.create(Exam(user_id=user.id, title="Exam 1", subject="Math"))
        await repo.create(Exam(user_id=user.id, title="Exam 2", subject="Physics"))
        
        # Act
        count = await repo.count_by_user(user.id)
        
        # Assert
        assert count == 2
