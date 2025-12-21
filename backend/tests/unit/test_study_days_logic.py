from datetime import datetime, timedelta, timezone
from uuid import uuid4
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class MockExam:
    id: uuid4
    exam_date: datetime

@dataclass
class MockTopic:
    id: uuid4
    topic_name: str
    order_index: int
    scheduled_date: Optional[datetime] = None

# Pure logic test of StudyPlannerService.schedule_exam
def test_study_days_logic():
    print("Testing Study Days Logic...")
    
    # Thursday, 2025-12-25
    exam_date = datetime(2025, 12, 25, tzinfo=timezone.utc)
    exam = MockExam(id=uuid4(), exam_date=exam_date)
    
    topics = [
        MockTopic(id=uuid4(), topic_name="Topic 1", order_index=0),
        MockTopic(id=uuid4(), topic_name="Topic 2", order_index=1),
        MockTopic(id=uuid4(), topic_name="Topic 3", order_index=2),
    ]
    
    # We simulate a "now" date of Monday, 2025-12-22
    # Days in week: Mon(0), Tue(1), Wed(2), Thu(3), Fri(4), Sat(5), Sun(6)
    
    # Scenario: User only wants to study on Mon(0) and Wed(2)
    study_days = [0, 2]
    
    from app.services.study_planner_service import StudyPlannerService
    # We'll need to mock 'datetime.now' in the service or adjust our test to its behavior
    # Actually, let's just run it and see how it behaves with the real 'now'
    
    planner = StudyPlannerService()
    # Note: StudyPlannerService uses datetime.now(timezone.utc)
    # If today is Sunday(6), and we set study days to [0, 2], 
    # the first topic should land on Monday.
    
    updated = planner.schedule_exam(exam, topics, study_days=study_days, revision_buffer_days=0)
    
    for t in updated:
        print(f"Topic: {t.topic_name}, Scheduled: {t.scheduled_date} (Weekday: {t.scheduled_date.weekday()})")
        assert t.scheduled_date.weekday() in study_days
    
    print("Study Days Logic Test Passed!")

if __name__ == "__main__":
    # Import path setup if needed, but since we are in the environment it might work
    try:
        test_study_days_logic()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
