from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

import pytest

from app.domain.review import ReviewItem
from app.services.study_service import StudyService


@pytest.fixture
def mock_review_repo():
    return AsyncMock()


@pytest.fixture
def mock_session_repo():
    return AsyncMock()


@pytest.fixture
def study_service(mock_review_repo, mock_session_repo):
    return StudyService(mock_review_repo, mock_session_repo)


@pytest.mark.asyncio
class TestStudyService:

    async def test_get_due_reviews(self, study_service, mock_review_repo):
        # Arrange
        user_id = uuid4()
        items = [ReviewItem(user_id=user_id, question="Question 1", answer="Answer 1")]
        mock_review_repo.list_due_by_user.return_value = items

        # Act
        result = await study_service.get_due_reviews(user_id, limit=10, interleave=False)

        # Assert
        assert len(result) == 1
        assert result[0].question == "Question 1"
        mock_review_repo.list_due_by_user.assert_called_once_with(user_id, 10)

    async def test_submit_review_success(self, study_service, mock_review_repo):
        # Arrange
        user_id = uuid4()
        item_id = uuid4()
        item = ReviewItem(
            id=item_id, user_id=user_id, question="Question", answer="Answer"
        )
        mock_review_repo.get_by_id.return_value = item
        mock_review_repo.update.return_value = item

        # Act
        result = await study_service.submit_review(user_id, item_id, quality=3)

        # Assert
        assert result.reps == 1
        assert (
            result.state == "learning"
        )  # First review with 3 (Good) -> learning step 1
        mock_review_repo.update.assert_called_once()

    async def test_submit_review_not_found(self, study_service, mock_review_repo):
        # Arrange
        mock_review_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Review item not found"):
            await study_service.submit_review(uuid4(), uuid4(), 3)

    async def test_submit_review_unauthorized(self, study_service, mock_review_repo):
        # Arrange
        user_id = uuid4()
        other_user_id = uuid4()
        item = ReviewItem(user_id=other_user_id, question="Question", answer="Answer")
        mock_review_repo.get_by_id.return_value = item

        # Act & Assert
        with pytest.raises(ValueError, match="Unauthorized"):
            await study_service.submit_review(user_id, uuid4(), 3)

    async def test_interleaved_reviews(self, study_service, mock_review_repo):
        # Arrange
        user_id = uuid4()
        topic_a = uuid4()
        topic_b = uuid4()
        
        # Create mock items
        items = []
        # 5 items from Topic A
        for _ in range(5):
            items.append(ReviewItem(
                id=uuid4(), user_id=user_id, topic_id=topic_a,
                question="Question A", answer="Answer A", stability=1.0, difficulty=1.0,
                elapsed_days=1, scheduled_days=1, reps=1, lapses=0,
                state="review", next_review_date=datetime.utcnow(), created_at=datetime.utcnow()
            ))
        # 5 items from Topic B
        for _ in range(5):
            items.append(ReviewItem(
                id=uuid4(), user_id=user_id, topic_id=topic_b,
                question="Question B", answer="Answer B", stability=1.0, difficulty=1.0,
                elapsed_days=1, scheduled_days=1, reps=1, lapses=0,
                state="review", next_review_date=datetime.utcnow(), created_at=datetime.utcnow()
            ))
            
        # Mock repository return
        mock_review_repo.list_due_by_user.return_value = items
        
        # Act
        result = await study_service.get_due_reviews(
            user_id=user_id, 
            limit=10, 
            interleave=True, 
            topic_mix_count=2
        )
        
        # Assert
        assert len(result) == 10
        
        # Verify mixing: check if we have items from both topics
        topics_found = set(item.topic_id for item in result)
        assert len(topics_found) == 2
        assert topic_a in topics_found
        assert topic_b in topics_found
        
        # Verify it's not just AAAAA BBBBB (simple check for at least one switch)
        switches = 0
        for i in range(len(result) - 1):
            if result[i].topic_id != result[i+1].topic_id:
                switches += 1
                
        # With perfect interleaving A B A B A B... we expect 9 switches
        # With random shuffle, we expect at least some switches
        assert switches > 0
