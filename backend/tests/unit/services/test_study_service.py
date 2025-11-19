import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4
from datetime import datetime
from app.services.study_service import StudyService
from app.domain.review import ReviewItem, Rating

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
        result = await study_service.get_due_reviews(user_id, limit=10)
        
        # Assert
        assert len(result) == 1
        assert result[0].question == "Question 1"
        mock_review_repo.list_due_by_user.assert_called_once_with(user_id, 10)

    async def test_submit_review_success(self, study_service, mock_review_repo):
        # Arrange
        user_id = uuid4()
        item_id = uuid4()
        item = ReviewItem(id=item_id, user_id=user_id, question="Question", answer="Answer")
        mock_review_repo.get_by_id.return_value = item
        mock_review_repo.update.return_value = item
        
        # Act
        result = await study_service.submit_review(user_id, item_id, quality=3)
        
        # Assert
        assert result.reps == 1
        assert result.state == "learning" # First review with 3 (Good) -> learning step 1
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
