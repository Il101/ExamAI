from datetime import datetime, timedelta, timezone
from uuid import uuid4
from dataclasses import dataclass, field
from typing import List, Optional

# Minimal Domain models for testing
@dataclass
class MockExam:
    id: uuid4
    user_id: uuid4
    course_id: Optional[uuid4]
    exam_date: Optional[datetime]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "ready"

@dataclass
class MockTopic:
    id: uuid4
    exam_id: uuid4
    topic_name: str
    quiz_completed: bool
    scheduled_date: Optional[datetime] = None
    order_index: int = 0

# Mock Services
class MockStudyPlannerService:
    def schedule_exam(self, exam: MockExam, topics: List[MockTopic]) -> List[MockTopic]:
        now = datetime.now(timezone.utc)
        for i, topic in enumerate(topics):
            topic.scheduled_date = now + timedelta(days=i)
        return topics

# Test Logic
def test_course_reschedule_logic():
    print("Starting course logic test...")
    
    user_id = uuid4()
    course_id = uuid4()
    
    # Exam 1 (Older)
    exam1 = MockExam(id=uuid4(), user_id=user_id, course_id=course_id, 
                     exam_date=None, created_at=datetime.now(timezone.utc) - timedelta(hours=2))
    t1_1 = MockTopic(id=uuid4(), exam_id=exam1.id, topic_name="E1-T1", quiz_completed=False)
    
    # Exam 2 (Newer, has date)
    exam2 = MockExam(id=uuid4(), user_id=user_id, course_id=course_id, 
                     exam_date=datetime.now(timezone.utc) + timedelta(days=10),
                     created_at=datetime.now(timezone.utc) - timedelta(hours=1))
    t2_1 = MockTopic(id=uuid4(), exam_id=exam2.id, topic_name="E2-T1", quiz_completed=False)
    
    exams_in_course = [exam1, exam2]
    
    # Simulate ExamService.reschedule_exam_topics logic
    print(f"Triggering reschedule for Exam 2 in Course {course_id}")
    
    # 1. Fetch exams in course, sort by created_at
    sorted_exams = sorted(exams_in_course, key=lambda e: e.created_at)
    assert sorted_exams[0].id == exam1.id
    
    # 2. Collect incomplete topics
    all_incomplete = []
    topics_map = {exam1.id: [t1_1], exam2.id: [t2_1]}
    
    for e in sorted_exams:
        all_incomplete.extend([t for t in topics_map[e.id] if not t.quiz_completed])
    
    assert len(all_incomplete) == 2
    assert all_incomplete[0].topic_name == "E1-T1" # Oldest exam first
    
    # 3. Schedule
    planner = MockStudyPlannerService()
    updated = planner.schedule_exam(exam2, all_incomplete) # Use exam2's date as target
    
    assert updated[0].topic_name == "E1-T1"
    assert updated[0].scheduled_date < updated[1].scheduled_date
    
    print("Course Logic Test Passed: Sequential scheduling across exams verified.")

if __name__ == "__main__":
    test_course_reschedule_logic()
