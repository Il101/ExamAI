# backend/tests/unit/domain/test_review.py
from datetime import datetime, timedelta

import pytest
from freezegun import freeze_time

from app.domain.review import ReviewItem


class TestReviewItem:

    def test_initialization(self):
        item = ReviewItem(question="What is Python?", answer="A programming language")
        assert item.state == "new"
        assert item.reps == 0
        assert item.lapses == 0
        assert item.stability == 0.0
        assert item.difficulty == 0.0
        assert item.scheduled_days == 0
        assert item.last_reviewed_at is None

    def test_validation_error(self):
        with pytest.raises(ValueError, match="Question must be at least 5 characters"):
            ReviewItem(question="Hi", answer="Answer")

        with pytest.raises(ValueError, match="Answer must be at least 2 characters"):
            ReviewItem(question="Valid Question", answer="A")

    @freeze_time("2024-01-01 12:00:00")
    def test_first_review_good_learning_steps(self):
        """Test learning steps: 1min -> 10min -> Graduate"""
        item = ReviewItem(question="Test Question", answer="Test Answer")

        # 1. First review: Good (3) -> Move to 10min step
        next_date = item.review(rating=3)

        assert item.state == "learning"
        assert item.current_step_index == 1
        assert item.reps == 1
        # Should be scheduled for 10 minutes later
        assert next_date == datetime(2024, 1, 1, 12, 10, 0)

        # 2. Second review (after 10 mins): Good (3) -> Graduate
        with freeze_time("2024-01-01 12:10:00"):
            next_date = item.review(rating=3)

            assert item.state == "review"
            assert item.reps == 2
            # Should be scheduled for days now (FSRS calculation)
            assert item.scheduled_days >= 1
            assert next_date > datetime(2024, 1, 1, 12, 10, 0) + timedelta(hours=23)

    @freeze_time("2024-01-01 12:00:00")
    def test_first_review_easy_graduates_immediately(self):
        """Test Easy (4) skips learning steps"""
        item = ReviewItem(question="Test Question", answer="Test Answer")

        # First review: Easy (4)
        item.review(rating=4)

        assert item.state == "review"
        assert item.reps == 1
        assert item.scheduled_days >= 1

    @freeze_time("2024-01-01 12:00:00")
    def test_learning_step_reset_on_again(self):
        """Test Again (1) resets learning steps"""
        item = ReviewItem(question="Test Question", answer="Test Answer")

        # 1. Good (3) -> Step 2 (10min)
        item.review(rating=3)
        assert item.current_step_index == 1

        # 2. Again (1) -> Reset to Step 1 (1min)
        with freeze_time("2024-01-01 12:10:00"):
            next_date = item.review(rating=1)

            assert item.state == "learning"
            assert item.current_step_index == 0
            assert next_date == datetime(2024, 1, 1, 12, 11, 0)  # +1 min

    @freeze_time("2024-01-01 12:00:00")
    def test_first_review_again(self):
        item = ReviewItem(question="Test Question", answer="Test Answer")

        # First review: Again (1)
        next_date = item.review(rating=1)

        assert item.state == "learning"
        assert item.reps == 1
        # Again on new card doesn't count as lapse in Anki usually, but here we can decide.
        # Code says: if state != "new": lapses += 1. So lapses should be 0.
        assert item.lapses == 0

        # Check FSRS initialization
        assert item.stability == 0.4

        # Scheduled for 1 min (first step)
        assert next_date == datetime(2024, 1, 1, 12, 1, 0)

    @freeze_time("2024-01-01 12:00:00")
    def test_subsequent_review(self):
        item = ReviewItem(question="Test Question", answer="Test Answer")

        # Graduate the card first
        item.review(rating=4)  # Easy -> Review
        assert item.state == "review"

        # Advance time by scheduled interval
        scheduled_days = item.scheduled_days
        with freeze_time(
            datetime(2024, 1, 1, 12, 0, 0) + timedelta(days=scheduled_days)
        ):
            # Review: Good (3)
            item.review(rating=3)

            assert item.reps == 2
            assert item.elapsed_days == scheduled_days

            # Stability should increase
            assert item.stability > 0.1

            # Difficulty should have decreased because we rated it Easy (4) initially
            assert item.difficulty < 4.93

            assert item.scheduled_days > scheduled_days

    def test_is_due(self):
        item = ReviewItem(question="Question", answer="Answer")
        # New item is due immediately (next_review_date defaults to now)
        assert item.is_due() is True

        item.next_review_date = datetime.utcnow() + timedelta(hours=1)
        assert item.is_due() is False

        item.next_review_date = datetime.utcnow() - timedelta(hours=1)
        assert item.is_due() is True

    def test_success_rate(self):
        item = ReviewItem(question="Question", answer="Answer")
        assert item.get_success_rate() == 0.0

        item.review(3)  # Success
        assert item.get_success_rate() == 1.0

        item.review(1)  # Fail
        assert item.get_success_rate() == 0.5  # 1 success / 2 reps

    def test_reset(self):
        item = ReviewItem(question="Question", answer="Answer")
        item.review(3)
        item.reset()

        assert item.state == "new"
        assert item.reps == 0
        assert item.stability == 0.0
        assert item.last_reviewed_at is None
