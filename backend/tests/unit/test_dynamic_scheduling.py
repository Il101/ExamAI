import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from unittest.mock import MagicMock, AsyncMock

from app.domain.exam import Exam
from app.domain.topic import Topic
from app.services.exam_service import ExamService

@pytest.mark.asyncio
async def test_reschedule_exam_topics():
    # Setup
    user_id = uuid4()
    exam_id = uuid4()
    exam_date = datetime.now(timezone.utc) + timedelta(days=10)
    
    exam = Exam(
        id=exam_id,
        user_id=user_id,
        title="Test Exam",
        subject="Testing",
        exam_date=exam_date,
        status="ready"
    )
    
    # Topic 1: Completed (should not be rescheduled)
    t1_id = uuid4()
    t1 = Topic(
        id=t1_id,
        exam_id=exam_id,
        topic_name="Topic 1",
        quiz_completed=True,
        scheduled_date=datetime.now(timezone.utc) - timedelta(days=5)
    )
    
    # Topic 2: Incomplete (should be rescheduled)
    t2_id = uuid4()
    t2 = Topic(
        id=t2_id,
        exam_id=exam_id,
        topic_name="Topic 2",
        quiz_completed=False,
        scheduled_date=datetime.now(timezone.utc) - timedelta(days=1)
    )
    
    # Mocks
    exam_repo = MagicMock()
    exam_repo.get_by_user_and_id = AsyncMock(return_value=exam)
    exam_repo.update = AsyncMock(return_value=exam)
    exam_repo.session = MagicMock()
    exam_repo.session.flush = AsyncMock()
    
    llm = MagicMock()
    cost_guard = MagicMock()
    
    service = ExamService(exam_repo, cost_guard, llm)
    
    # Mock TopicRepository inside the method
    # Note: Since TopicRepository is imported inside the method, we'd normally use patch
    # But for a quick unit test we can check the logic by observing output
    
    with MagicMock() as mock_repo_class:
        topic_repo_instance = MagicMock()
        topic_repo_instance.get_by_exam_id = AsyncMock(return_value=[t1, t2])
        topic_repo_instance.update = AsyncMock()
        
        # We need to patch app.repositories.topic_repository.TopicRepository
        import app.services.exam_service
        from unittest.mock import patch
        
        with patch("app.services.exam_service.TopicRepository", return_value=topic_repo_instance):
            updated_topics = await service.reschedule_exam_topics(user_id, exam_id)
            
            # Assertions
            assert len(updated_topics) == 2
            # t1 should NOT have been updated (its date remains in the past)
            # t2 SHOULD have been updated to something new (likely today/now)
            
            # Check calls to topic_repo.update
            # It should only be called once for Topic 2
            assert topic_repo_instance.update.call_count == 1
            call_args = topic_repo_instance.update.call_args[0][0]
            assert call_args.id == t2_id
            assert call_args.scheduled_date > datetime.now(timezone.utc) - timedelta(minutes=1)
            
            print("Unit test passed: Only incomplete topics were rescheduled.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_reschedule_exam_topics())
