from typing import Any, Dict, List
from uuid import UUID
from datetime import date, timedelta
import random

from app.domain.review import Rating, ReviewItem
from app.domain.study_session import StudySession
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.study_session_repository import StudySessionRepository
from app.schemas.analytics import (
    AnalyticsResponse,
    DailyProgress,
    RetentionPoint,
    HeatmapPoint,
)


class StudyService:
    """
    Service for spaced repetition and study sessions.
    Implements FSRS algorithm workflow.
    """

    def __init__(
        self, review_repo: ReviewItemRepository, session_repo: StudySessionRepository
    ):
        self.review_repo = review_repo
        self.session_repo = session_repo

    # Review Items

    async def get_due_reviews(self, user_id: UUID, limit: int = 20) -> List[ReviewItem]:
        """
        Get review items due for study.

        Args:
            user_id: User ID
            limit: Max items to return

        Returns:
            List of due review items, ordered by priority
        """
        return await self.review_repo.list_due_by_user(user_id, limit)

    async def submit_review(
        self, user_id: UUID, review_item_id: UUID, quality: Rating
    ) -> ReviewItem:
        """
        Submit review response and update FSRS algorithm.

        Args:
            user_id: User ID
            review_item_id: Review item ID
            quality: Quality rating (1-4)

        Returns:
            Updated review item with new schedule
        """
        # Get review item
        item = await self.review_repo.get_by_id(review_item_id)

        if not item:
            raise ValueError("Review item not found")

        if item.user_id != user_id:
            raise ValueError("Unauthorized")

        # Apply FSRS algorithm
        item.review(quality)

        # Save updated item
        updated = await self.review_repo.update(item)

        return updated

    async def get_study_statistics(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user's study statistics.

        Returns:
            {
                "total_reviews": 150,
                "reviews_due": 12,
                "success_rate": 0.85,
                "streak_days": 7
            }
        """
        reviews_due = await self.review_repo.count_due_by_user(user_id)

        return {
            "total_reviews": 150,  # Placeholder
            "reviews_due": reviews_due,
            "success_rate": 0.85,  # Placeholder
            "streak_days": 3,  # Placeholder
        }

    async def get_analytics(self, user_id: UUID) -> AnalyticsResponse:
        """
        Get comprehensive analytics for dashboard.
        Currently returns mock data for visualization.
        """
        # TODO: Implement real aggregation queries in repositories

        today = date.today()

        # Mock Daily Progress (Last 7 days)
        daily_progress = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            daily_progress.append(
                DailyProgress(
                    date=day,
                    cards_reviewed=random.randint(10, 50),
                    cards_learned=random.randint(5, 20),
                    minutes_studied=random.randint(15, 60),
                )
            )

        # Mock Retention Curve
        retention_curve = [
            RetentionPoint(days_since_review=1, retention_rate=1.0),
            RetentionPoint(days_since_review=3, retention_rate=0.9),
            RetentionPoint(days_since_review=7, retention_rate=0.75),
            RetentionPoint(days_since_review=14, retention_rate=0.6),
            RetentionPoint(days_since_review=30, retention_rate=0.45),
        ]

        # Mock Heatmap (Last 30 days)
        activity_heatmap = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            count = random.randint(0, 20)
            level = 0
            if count > 0:
                level = 1
            if count > 5:
                level = 2
            if count > 10:
                level = 3
            if count > 15:
                level = 4

            activity_heatmap.append(HeatmapPoint(date=day, count=count, level=level))

        return AnalyticsResponse(
            daily_progress=daily_progress,
            retention_curve=retention_curve,
            activity_heatmap=activity_heatmap,
            total_cards_learned=142,
            total_minutes_studied=1250,
            current_streak=3,
            longest_streak=12,
        )

    # Study Sessions

    async def start_study_session(
        self, user_id: UUID, exam_id: UUID, pomodoro_duration: int = 25
    ) -> StudySession:
        """
        Start new study session.

        Args:
            user_id: User ID
            exam_id: Exam ID to study
            pomodoro_duration: Pomodoro duration in minutes

        Returns:
            Created study session
        """
        # Check if there is an active session
        active_session = await self.session_repo.get_active_by_user(user_id)
        if active_session:
            # Option: return existing or error. Let's return existing.
            return active_session

        session = StudySession(
            user_id=user_id,
            exam_id=exam_id,
            pomodoro_duration_minutes=pomodoro_duration,
            is_active=True,
        )

        created = await self.session_repo.create(session)

        return created

    async def complete_pomodoro(self, user_id: UUID, session_id: UUID) -> StudySession:
        """Mark pomodoro as completed"""
        session = await self.session_repo.get_by_id(session_id)

        if not session or session.user_id != user_id:
            raise ValueError("Session not found")

        session.complete_pomodoro()

        updated = await self.session_repo.update(session)

        return updated

    async def end_study_session(self, user_id: UUID, session_id: UUID) -> StudySession:
        """End study session"""
        session = await self.session_repo.get_by_id(session_id)

        if not session or session.user_id != user_id:
            raise ValueError("Session not found")

        session.end_session()

        updated = await self.session_repo.update(session)

        return updated
