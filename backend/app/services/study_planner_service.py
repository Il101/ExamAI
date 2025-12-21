from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from app.domain.exam import Exam
from app.domain.topic import Topic

class StudyPlannerService:
    """
    Service for automated study scheduling.
    Distributes topics across a timeframe leading to the exam date.
    """

    def schedule_exam(
        self, 
        course, # Course entity
        topics: List[Topic], 
        revision_buffer_days: int = 2,
        study_days: List[int] = None # 0-6 = Mon-Sun
    ) -> List[Topic]:
        """
        Distribute topics across the available study window, respecting chosen study days.
        Uses course.exam_date as the deadline.
        """
        if not course.exam_date:
            return topics

        if study_days is None:
            study_days = [0, 1, 2, 3, 4, 5, 6] # Default to all days

        now = datetime.now(timezone.utc)
        exam_date = course.exam_date
        
        if exam_date.tzinfo is None:
            exam_date = exam_date.replace(tzinfo=timezone.utc)

        # Calculate study end date (exam_date - buffer)
        study_end_date = exam_date - timedelta(days=revision_buffer_days)
        
        if study_end_date <= now:
            study_end_date = exam_date
            
        # Filter available dates between now and study_end_date
        available_dates = []
        current_date = now
        while current_date <= study_end_date:
            if current_date.weekday() in study_days:
                available_dates.append(current_date)
            current_date += timedelta(days=1)

        num_topics = len(topics)
        if num_topics == 0:
            return topics

        # Sort topics by order_index
        sorted_topics = sorted(topics, key=lambda t: t.order_index)

        num_available_days = len(available_dates)
        if num_available_days == 0:
            # If no days are selected, just schedule everything for today
            for topic in sorted_topics:
                topic.scheduled_date = now
            return sorted_topics

        if num_available_days >= num_topics:
            # Spread them out across available dates
            for i, topic in enumerate(sorted_topics):
                date_idx = i if i < num_available_days else num_available_days - 1
                topic.scheduled_date = available_dates[date_idx]
        else:
            # More topics than days: stack them
            topics_per_day = num_topics / num_available_days
            for i, topic in enumerate(sorted_topics):
                date_idx = int(i / topics_per_day)
                if date_idx >= num_available_days:
                    date_idx = num_available_days - 1
                topic.scheduled_date = available_dates[date_idx]

        return sorted_topics
