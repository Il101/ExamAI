from typing import Any, Dict, List
from uuid import UUID
from datetime import date, timedelta, datetime, timezone

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


from app.domain.review_log import ReviewLog
from app.repositories.review_log_repository import ReviewLogRepository

class StudyService:
    """
    Service for spaced repetition and study sessions.
    Implements FSRS algorithm workflow.
    """

    def __init__(
        self, 
        review_repo: ReviewItemRepository, 
        session_repo: StudySessionRepository,
        review_log_repo: ReviewLogRepository,
        quiz_result_repo: 'QuizResultRepository'
    ):
        self.review_repo = review_repo
        self.session_repo = session_repo
        self.review_log_repo = review_log_repo
        self.quiz_result_repo = quiz_result_repo

    # Review Items

    async def get_due_reviews(
        self, 
        user_id: UUID, 
        limit: int = 20,
        exam_id: UUID | None = None,
        topic_id: UUID | None = None
    ) -> List[ReviewItem]:
        """
        Get review items due for study.

        Args:
            user_id: User ID
            limit: Max items to return
            exam_id: Optional filter by Exam
            topic_id: Optional filter by Topic

        Returns:
            List of due review items, ordered by priority
        """
        return await self.review_repo.list_due_by_user(
            user_id=user_id, 
            limit=limit,
            exam_id=exam_id,
            topic_id=topic_id
        )

    async def submit_review(
        self, user_id: UUID, review_item_id: UUID, quality: Rating
    ) -> ReviewItem:
        """
        Submit review response and update FSRS algorithm.
        
        Uses transaction to ensure ReviewItem and ReviewLog are saved atomically.

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

        try:
            # Apply FSRS algorithm
            item.review(quality)

            # Save updated item (uses flush, not commit)
            updated = await self.review_repo.update(item)
            
            # Create Review Log (uses flush, not commit)
            # NOTE: passing naive datetime because ReviewLogModel.review_time was created without timezone=True
            review_time_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            
            log = ReviewLog(
                user_id=user_id,
                review_item_id=review_item_id,
                rating=quality,
                review_time=review_time_naive,
                interval_days=item.elapsed_days,
                scheduled_days=item.scheduled_days,
                stability=item.stability,
                difficulty=item.difficulty
            )
            await self.review_log_repo.add_log(log)
            
            # Both operations succeed - get_db() will commit
            return updated
            
        except Exception as e:
            # Rollback on any error to maintain data consistency
            await self.review_repo.session.rollback()
            raise ValueError(f"Failed to submit review: {str(e)}") from e

    async def get_next_intervals_preview(
        self, user_id: UUID, review_item_id: UUID
    ) -> dict[str, int]:
        """
        Preview intervals for all possible ratings.
        Shows user: "If you rate this as Good, next review in 5 days"

        Args:
            user_id: User ID
            review_item_id: Review item ID

        Returns:
            {
                "again": 1,   # days or minutes
                "hard": 3,
                "good": 7,
                "easy": 14
            }
        """
        item = await self.review_repo.get_by_id(review_item_id)

        if not item or item.user_id != user_id:
            raise ValueError("Review item not found")

        # Calculate intervals for each rating
        intervals = {}
        
        for rating in [1, 2, 3, 4]:
            # Create a copy of the item to simulate the review
            from copy import deepcopy
            temp_item = deepcopy(item)
            
            # Apply rating to get next interval
            temp_item.review(rating)
            
            # Determine if result is in minutes (learning) or days (review)
            if temp_item.state in ("learning", "relearning"):
                # Learning steps are in minutes
                intervals[self._rating_name(rating)] = temp_item.scheduled_days or 1
            else:
                # Review state uses days
                intervals[self._rating_name(rating)] = temp_item.scheduled_days
        
        return intervals
    
    def _rating_name(self, rating: int) -> str:
        """Convert rating number to name"""
        names = {1: "again", 2: "hard", 3: "good", 4: "easy"}
        return names.get(rating, "good")

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
        current_streak, _ = await self.session_repo.get_streak_stats(user_id)

        return {
            "total_reviews": 0,  # Placeholder until we add total count to log repo if needed
            "reviews_due": reviews_due,
            "success_rate": 0.0,
            "streak_days": current_streak,
        }

    async def get_analytics(self, user_id: UUID) -> AnalyticsResponse:
        """
        Get comprehensive analytics for dashboard.
        Uses real data from repositories.
        """

        # 1. Get Daily Progress (Last 7 days) from review logs AND quiz results
        daily_reviews = await self.review_log_repo.get_daily_activity(user_id, days=7)
        daily_minutes = await self.session_repo.get_daily_study_minutes(user_id, days=7)
        daily_quizzes = await self.quiz_result_repo.get_daily_activity(user_id, days=7)

        # Map to dictionary for easier lookup by date
        reviews_map = {r["date"]: r for r in daily_reviews}
        minutes_map = {r["date"]: r["minutes"] for r in daily_minutes}
        quizzes_map = {q["date"]: q for q in daily_quizzes}

        daily_progress = []
        today = date.today()
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            review_data = reviews_map.get(day, {"count": 0, "learned": 0})
            quiz_data = quizzes_map.get(day, {"questions_correct": 0})
            minutes = minutes_map.get(day, 0)

            # Combine flashcard reviews + quiz correct answers
            total_cards = review_data["count"] + quiz_data["questions_correct"]
            total_learned = review_data["learned"] + quiz_data["questions_correct"]

            daily_progress.append(
                DailyProgress(
                    date=day,
                    cards_reviewed=total_cards,
                    cards_learned=total_learned,
                    minutes_studied=minutes,
                )
            )

        # 2. Retention Curve
        retention_curve = await self.review_log_repo.get_retention_stats(user_id)
        
        # 3. Activity Heatmap (Last 30 days) from review logs AND quiz results
        heatmap_reviews = await self.review_log_repo.get_daily_activity(user_id, days=30)
        heatmap_quizzes = await self.quiz_result_repo.get_daily_activity(user_id, days=30)
        
        heatmap_reviews_map = {r["date"]: r["count"] for r in heatmap_reviews}
        heatmap_quizzes_map = {q["date"]: q["questions_correct"] for q in heatmap_quizzes}

        activity_heatmap = []
        for i in range(29, -1, -1):
            day = today - timedelta(days=i)
            review_count = heatmap_reviews_map.get(day, 0)
            quiz_count = heatmap_quizzes_map.get(day, 0)
            count = review_count + quiz_count

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

        # 4. Aggregates
        total_learned = await self.review_repo.count_total_learned(user_id)
        total_minutes = await self.session_repo.get_total_study_minutes(user_id)
        
        # Include quiz statistics
        quiz_stats = await self.quiz_result_repo.get_user_stats(user_id)
        total_cards_with_quizzes = total_learned + quiz_stats["questions_correct"]
        
        # Streaks
        current_streak, longest_streak = await self.session_repo.get_streak_stats(user_id)

        return AnalyticsResponse(
            daily_progress=daily_progress,
            retention_curve=retention_curve,
            activity_heatmap=activity_heatmap,
            total_cards_learned=total_cards_with_quizzes,
            total_minutes_studied=total_minutes,
            current_streak=current_streak,
            longest_streak=longest_streak,
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
