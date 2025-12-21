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
        exam: Exam, 
        topics: List[Topic], 
        revision_buffer_days: int = 2
    ) -> List[Topic]:
        """
        Distribute topics across the available study window.
        
        Args:
            exam: The exam entity (must have exam_date)
            topics: List of topics to schedule
            revision_buffer_days: Days to leave for final revision before exam
            
        Returns:
            Updated topics with scheduled_date set
        """
        if not exam.exam_date:
            return topics

        now = datetime.now(timezone.utc)
        exam_date = exam.exam_date
        
        if exam_date.tzinfo is None:
            exam_date = exam_date.replace(tzinfo=timezone.utc)

        # Calculate study end date (exam_date - buffer)
        study_end_date = exam_date - timedelta(days=revision_buffer_days)
        
        # If exam is too soon, adjust buffer or just use today
        if study_end_date <= now:
            study_end_date = exam_date
            
        available_days = (study_end_date - now).days + 1
        num_topics = len(topics)
        
        if num_topics == 0:
            return topics

        # Sort topics by order_index just in case
        sorted_topics = sorted(topics, key=lambda t: t.order_index)

        if available_days >= num_topics:
            # More days than topics: spread them out (one or fewer per day)
            # For simplicity, we'll aim for 1 topic per day starting today
            for i, topic in enumerate(sorted_topics):
                day_offset = i
                if day_offset >= available_days:
                    day_offset = available_days - 1
                topic.scheduled_date = now + timedelta(days=day_offset)
        else:
            # More topics than days: stack them (multiple topics per day)
            topics_per_day = num_topics / available_days
            for i, topic in enumerate(sorted_topics):
                day_offset = int(i / topics_per_day)
                topic.scheduled_date = now + timedelta(days=day_offset)

        return sorted_topics
