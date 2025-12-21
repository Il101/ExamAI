from datetime import datetime, timedelta, timezone
from uuid import uuid4
from dataclasses import dataclass, field
from typing import List, Optional

# Minimal Domain models for testing
@dataclass
class MockExam:
    id: uuid4
    exam_date: datetime
    status: str = "ready"

@dataclass
class MockTopic:
    id: uuid4
    topic_name: str
    quiz_completed: bool
    scheduled_date: Optional[datetime] = None
    order_index: int = 0

# Minimal Planner logic
class MockStudyPlannerService:
    def schedule_exam(self, exam: MockExam, topics: List[MockTopic]) -> List[MockTopic]:
        now = datetime.now(timezone.utc)
        for i, topic in enumerate(topics):
            topic.scheduled_date = now + timedelta(days=i)
        return topics

# Test Logic
def test_reschedule_logic():
    print("Starting pure logic test...")
    
    exam_id = uuid4()
    exam = MockExam(id=exam_id, exam_date=datetime.now(timezone.utc) + timedelta(days=10))
    
    t1 = MockTopic(id=uuid4(), topic_name="T1", quiz_completed=True, scheduled_date=datetime.now(timezone.utc) - timedelta(days=5))
    t2 = MockTopic(id=uuid4(), topic_name="T2", quiz_completed=False, scheduled_date=datetime.now(timezone.utc) - timedelta(days=1))
    t3 = MockTopic(id=uuid4(), topic_name="T3", quiz_completed=False, scheduled_date=None)
    
    all_topics = [t1, t2, t3]
    
    # Filter for reschedule
    incomplete_topics = [t for t in all_topics if not t.quiz_completed]
    assert len(incomplete_topics) == 2
    assert t1 not in incomplete_topics
    
    # Schedule
    planner = MockStudyPlannerService()
    updated_topics = planner.schedule_exam(exam, incomplete_topics)
    
    assert len(updated_topics) == 2
    assert updated_topics[0].topic_name == "T2"
    assert updated_topics[0].scheduled_date > datetime.now(timezone.utc) - timedelta(seconds=10)
    
    print("Logic Test Passed!")

if __name__ == "__main__":
    test_reschedule_logic()
