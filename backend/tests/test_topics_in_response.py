"""Quick test to verify topics are returned in exam response"""

from datetime import datetime
from uuid import uuid4

import pytest

from app.schemas.exam import ExamResponse
from app.schemas.topic import TopicResponse


def test_exam_response_with_topics():
    """Test that ExamResponse can include topics"""
    exam_id = uuid4()
    user_id = uuid4()

    # Create topic
    topic = TopicResponse(
        id=uuid4(),
        exam_id=exam_id,
        topic_name="Test Topic",
        content="Test content",
        order_index=0,
        difficulty_level=1,
        estimated_study_minutes=30,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    # Create exam response with topics
    exam_response = ExamResponse(
        id=exam_id,
        user_id=user_id,
        title="Test Exam",
        subject="Testing",
        exam_type="written",
        level="bachelor",
        status="ready",
        topic_count=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        topics=[topic],
    )

    assert len(exam_response.topics) == 1
    assert exam_response.topics[0].topic_name == "Test Topic"

    print("✅ ExamResponse with topics works correctly!")


if __name__ == "__main__":
    test_exam_response_with_topics()
