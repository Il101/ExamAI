from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.exam import Exam
from app.domain.study_session import StudySession
from app.domain.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.study_session_repository import StudySessionRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestStudySessionRepository:

    async def create_user(self, session):
        repo = UserRepository(session)
        user = User(email=f"test_{uuid4()}@example.com", full_name="Test User")
        return await repo.create(user)

    async def create_exam(self, session, user_id):
        repo = ExamRepository(session)
        exam = Exam(
            user_id=user_id, title="Test Exam", subject="Testing", status="draft"
        )
        return await repo.create(exam)

    async def test_create_and_get(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        exam = await self.create_exam(test_session, user.id)
        repo = StudySessionRepository(test_session)

        session = StudySession(
            user_id=user.id, exam_id=exam.id, pomodoro_duration_minutes=30
        )

        # Act
        created = await repo.create(session)
        retrieved = await repo.get_by_id(created.id)

        # Assert
        assert created.id is not None
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.user_id == user.id
        assert retrieved.pomodoro_duration_minutes == 30

    async def test_get_active_by_user(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        exam = await self.create_exam(test_session, user.id)
        repo = StudySessionRepository(test_session)

        # Active session (no ended_at)
        active_session = StudySession(
            user_id=user.id, exam_id=exam.id, started_at=datetime.utcnow()
        )
        # Ensure ended_at is None (default)

        # Inactive session (has ended_at)
        inactive_session = StudySession(
            user_id=user.id,
            exam_id=exam.id,
            started_at=datetime.utcnow() - timedelta(hours=2),
            ended_at=datetime.utcnow() - timedelta(hours=1),
            is_active=False,
        )

        await repo.create(inactive_session)
        await repo.create(active_session)

        # Act
        result = await repo.get_active_by_user(user.id)

        # Assert
        assert result is not None
        assert result.id == active_session.id
        assert result.ended_at is None

    async def test_list_by_user(self, test_session):
        # Arrange
        user = await self.create_user(test_session)
        exam = await self.create_exam(test_session, user.id)
        repo = StudySessionRepository(test_session)

        session1 = StudySession(user_id=user.id, exam_id=exam.id)
        session2 = StudySession(user_id=user.id, exam_id=exam.id)

        await repo.create(session1)
        await repo.create(session2)

        # Act
        sessions = await repo.list_by_user(user.id)

        # Assert
        assert len(sessions) == 2
        assert all(s.user_id == user.id for s in sessions)
