# backend/tests/unit/domain/test_exam.py
import pytest
from uuid import uuid4
from datetime import datetime
from app.domain.exam import Exam, ExamStatus, ExamType, ExamLevel

class TestExamDomain:
    """Unit tests for Exam domain model"""

    def test_create_exam(self):
        """Test creating a new exam"""
        exam = Exam(
            id=None,
            user_id=uuid4(),
            title="Calculus I Final",
            subject="Mathematics",
            exam_type="written",
            level="bachelor",
            original_content="Course notes..." * 10, # Ensure enough content
            created_at=datetime.now()
        )
        
        assert exam.status == "draft"
        assert exam.topic_count == 0
        assert exam.can_generate() is True

    def test_validation_error(self):
        """Test validation logic"""
        with pytest.raises(ValueError, match="Title must be at least 3 characters"):
            Exam(title="Hi", subject="Math")
            
        with pytest.raises(ValueError, match="Subject must be at least 2 characters"):
            Exam(title="Math", subject="A")

    def test_start_generation(self):
        """Test starting generation process"""
        exam = Exam(
            id=uuid4(),
            user_id=uuid4(),
            title="Test Exam",
            subject="Test",
            original_content="Content" * 20, # > 100 chars
            created_at=datetime.now()
        )
        
        exam.start_generation()
        
        assert exam.status == "generating"
        assert exam.can_generate() is False

    def test_cannot_generate_insufficient_content(self):
        """Test cannot generate with short content"""
        exam = Exam(
            title="Test",
            subject="Test",
            original_content="Short",
            status="draft"
        )
        assert exam.can_generate() is False
        
        with pytest.raises(ValueError, match="Cannot start generation"):
            exam.start_generation()

    def test_mark_as_ready(self):
        """Test marking exam as ready"""
        exam = Exam(
            title="Test",
            subject="Test",
            original_content="Content" * 20,
            status="generating"
        )
        
        exam.mark_as_ready(
            ai_summary="Summary",
            token_input=100,
            token_output=50,
            cost=0.05
        )
        
        assert exam.status == "ready"
        assert exam.ai_summary == "Summary"
        assert exam.generation_cost_usd == 0.05
        assert exam.token_count_input == 100

    def test_mark_as_failed(self):
        """Test marking exam as failed"""
        exam = Exam(
            title="Test",
            subject="Test",
            original_content="Content" * 20,
            status="generating"
        )
        
        exam.mark_as_failed()
        
        assert exam.status == "failed"
        # Failed exam can be retried
        assert exam.can_generate() is True

    def test_cannot_generate_when_generating(self):
        """Test that cannot start generation when already generating"""
        exam = Exam(
            title="Test",
            subject="Test",
            original_content="Content" * 20,
            status="generating"
        )
        
        assert exam.can_generate() is False
        
        with pytest.raises(ValueError):
            exam.start_generation()

    def test_archive(self):
        """Test archiving exam"""
        exam = Exam(
            title="Test",
            subject="Test",
            status="ready",
            ai_summary="Summary"
        )
        
        exam.archive()
        assert exam.status == "archived"

    def test_cannot_archive_generating(self):
        """Test cannot archive while generating"""
        exam = Exam(
            title="Test",
            subject="Test",
            status="generating"
        )
        
        with pytest.raises(ValueError, match="Cannot archive exam during generation"):
            exam.archive()

    def test_update_topic_count(self):
        """Test updating topic count"""
        exam = Exam(title="Test", subject="Test")
        exam.update_topic_count(5)
        assert exam.topic_count == 5
        
        with pytest.raises(ValueError):
            exam.update_topic_count(-1)
