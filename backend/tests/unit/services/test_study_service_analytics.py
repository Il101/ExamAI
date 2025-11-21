import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import date

from app.services.study_service import StudyService

class TestStudyServiceAnalytics:
    @pytest.fixture
    def mock_review_repo(self):
        return AsyncMock()

    @pytest.fixture
    def mock_session_repo(self):
        return AsyncMock()

    @pytest.fixture
    def service(self, mock_review_repo, mock_session_repo):
        return StudyService(mock_review_repo, mock_session_repo)

    @pytest.mark.asyncio
    async def test_get_analytics_uses_real_data(self, service, mock_review_repo, mock_session_repo):
        # Arrange
        user_id = uuid4()
        today = date.today()

        # Mock repo responses
        mock_review_repo.get_daily_activity.return_value = [
            {"date": today, "count": 10, "learned": 2}
        ]
        mock_session_repo.get_daily_study_minutes.return_value = [
            {"date": today, "minutes": 45}
        ]
        mock_review_repo.count_total_learned.return_value = 100
        mock_session_repo.get_total_study_minutes.return_value = 500

        # Act
        analytics = await service.get_analytics(user_id)

        # Assert
        assert analytics.total_cards_learned == 100
        assert analytics.total_minutes_studied == 500

        # Check if today's data is correctly mapped
        today_progress = next(p for p in analytics.daily_progress if p.date == today)
        assert today_progress.cards_reviewed == 10
        assert today_progress.cards_learned == 2
        assert today_progress.minutes_studied == 45

        # Verify repo calls
        mock_review_repo.get_daily_activity.assert_called()
        mock_session_repo.get_daily_study_minutes.assert_called()
        mock_review_repo.count_total_learned.assert_called_with(user_id)
        mock_session_repo.get_total_study_minutes.assert_called_with(user_id)
