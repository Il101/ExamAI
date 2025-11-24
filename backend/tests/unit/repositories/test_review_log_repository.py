import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from app.domain.review_log import ReviewLog
from app.repositories.review_log_repository import ReviewLogRepository

class TestReviewLogRepository:
    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return ReviewLogRepository(mock_session)

    @pytest.mark.asyncio
    async def test_add_log(self, repo, mock_session):
        # Arrange
        log = ReviewLog(
            user_id=uuid4(),
            review_item_id=uuid4(),
            rating=3,
            interval_days=1,
            scheduled_days=2,
            stability=1.5,
            difficulty=5.0
        )

        # Act
        await repo.add_log(log)

        # Assert
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_retention_stats_empty(self, repo, mock_session):
        # Arrange
        user_id = uuid4()
        mock_result = AsyncMock()
        mock_result.__iter__.return_value = []
        mock_session.execute.return_value = mock_result

        # Act
        stats = await repo.get_retention_stats(user_id)

        # Assert
        assert len(stats) == 5
        # Should return default theoretical curve or empty-based calculation
        # In our impl, empty buckets get 0.9^days
        assert stats[0].days_since_review == 1
        assert stats[0].retention_rate == 0.9
        assert stats[4].days_since_review == 30
        assert stats[4].retention_rate < 0.1 # 0.9^30 is small

    @pytest.mark.asyncio
    async def test_get_retention_stats_with_data(self, repo, mock_session):
        # Arrange
        user_id = uuid4()
        
        # Mock DB rows: interval_days, total, passed
        rows = [
            AsyncMock(interval_days=1, total=10, passed=9), # 90%
            AsyncMock(interval_days=3, total=10, passed=8), # 80%
            AsyncMock(interval_days=30, total=10, passed=5), # 50%
        ]
        
        mock_result = AsyncMock()
        mock_result.__iter__.return_value = rows
        mock_session.execute.return_value = mock_result

        # Act
        stats = await repo.get_retention_stats(user_id)

        # Assert
        # Bucket 1 (Day 1)
        assert stats[0].days_since_review == 1
        assert stats[0].retention_rate == 0.9
        
        # Bucket 2 (Day 3)
        assert stats[1].days_since_review == 3
        assert stats[1].retention_rate == 0.8
        
        # Bucket 5 (Day 30)
        assert stats[4].days_since_review == 30
        assert stats[4].retention_rate == 0.5
