"""
Unit tests for TopicContentGenerator.generate_batch() method.

These tests ensure parameter validation and prevent regression bugs like
the recent TypeError with unexpected 'user_id' keyword argument.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.services.content_generation.topic_generator import TopicContentGenerator


class TestTopicContentGeneratorGenerateBatch:
    """Tests for TopicContentGenerator.generate_batch() method"""

    @pytest.fixture
    def mock_executor(self):
        """Mock TopicExecutor"""
        mock = AsyncMock()
        mock.execute_batch.return_value = {}
        return mock

    @pytest.fixture
    def mock_flashcard_gen(self):
        """Mock FlashcardGenerator"""
        mock = AsyncMock()
        mock.MIN_CONTENT_LENGTH = 100
        mock.create_for_batch.return_value = ({}, {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0})
        return mock

    @pytest.fixture
    def mock_fallback_service(self):
        """Mock CacheFallbackService"""
        mock = AsyncMock()
        # execute_with_fallback returns (result, updated_cache_name)
        mock.execute_with_fallback.return_value = ({}, None)
        return mock

    @pytest.fixture
    def mock_topic_repo(self):
        """Mock TopicRepository"""
        mock = AsyncMock()
        mock.get_by_id.return_value = None
        return mock

    @pytest.fixture
    def mock_exam_repo(self):
        """Mock ExamRepository"""
        mock = AsyncMock()
        mock.get_by_id.return_value = None
        return mock

    @pytest.fixture
    def topic_generator(
        self,
        mock_executor,
        mock_flashcard_gen,
        mock_fallback_service,
        mock_topic_repo,
        mock_exam_repo
    ):
        """Create TopicContentGenerator instance with mocked dependencies"""
        return TopicContentGenerator(
            executor=mock_executor,
            flashcard_gen=mock_flashcard_gen,
            fallback_service=mock_fallback_service,
            topic_repo=mock_topic_repo,
            exam_repo=mock_exam_repo
        )

    @pytest.mark.asyncio
    async def test_generate_batch_with_valid_parameters(
        self,
        topic_generator,
        mock_topic_repo,
        mock_exam_repo
    ):
        """Test that generate_batch accepts correct parameters without errors"""
        # Setup
        exam_id = uuid4()
        topic_id = uuid4()
        
        # Mock topic
        mock_topic = Mock()
        mock_topic.id = topic_id
        mock_topic.exam_id = exam_id
        mock_topic.topic_name = "Test Topic"
        mock_topic.status = "pending"
        mock_topic.content = None
        mock_topic.user_id = uuid4()
        mock_topic_repo.get_by_id.return_value = mock_topic
        
        # Mock exam
        mock_exam = Mock()
        mock_exam.id = exam_id
        mock_exam.subject = "Physics"
        mock_exam.level = "bachelor"
        mock_exam.exam_type = "written"
        mock_exam.original_content = "Test content"
        mock_exam.cache_name = "test_cache"
        mock_exam_repo.get_by_id.return_value = mock_exam
        
        # Execute - verify no TypeError is raised
        result = await topic_generator.generate_batch(
            topic_ids=[topic_id],
            cache_name="test_cache",
            exam_id=exam_id,
            output_language="en",
            include_quizzes=True
        )
        
        # Verify
        assert isinstance(result, dict)
        assert "results" in result
        assert "usage" in result
        assert result["usage"]["tokens_input"] >= 0
        assert result["usage"]["tokens_output"] >= 0
        assert result["usage"]["cost_usd"] >= 0.0

    @pytest.mark.asyncio
    async def test_generate_batch_rejects_invalid_parameters(self, topic_generator):
        """
        CRITICAL TEST: Verify that generate_batch raises TypeError for invalid parameters.
        This test would have caught the recent bug where user_id was passed.
        """
        topic_id = uuid4()
        user_id = uuid4()
        
        # Execute & Verify - should raise TypeError for unexpected keyword argument
        with pytest.raises(TypeError, match="unexpected keyword argument"):
            await topic_generator.generate_batch(
                topic_ids=[topic_id],
                user_id=user_id,  # INVALID PARAMETER - should cause TypeError
                cache_name="test_cache"
            )

    @pytest.mark.asyncio
    async def test_generate_batch_empty_topics(self, topic_generator):
        """Test that generate_batch handles empty topic list gracefully"""
        # Execute
        result = await topic_generator.generate_batch(
            topic_ids=[],
            cache_name="test_cache"
        )
        
        # Verify - should return empty results without errors
        assert result == {
            "results": {},
            "usage": {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0.0}
        }

    @pytest.mark.asyncio
    async def test_generate_batch_with_fallback(
        self,
        topic_generator,
        mock_fallback_service,
        mock_topic_repo,
        mock_exam_repo
    ):
        """Test that generate_batch uses fallback service correctly"""
        # Setup
        exam_id = uuid4()
        topic_id = uuid4()
        
        mock_topic = Mock()
        mock_topic.id = topic_id
        mock_topic.exam_id = exam_id
        mock_topic.topic_name = "Test Topic"
        mock_topic.status = "pending"
        mock_topic.content = None
        mock_topic.user_id = uuid4()
        mock_topic_repo.get_by_id.return_value = mock_topic
        
        mock_exam = Mock()
        mock_exam.id = exam_id
        mock_exam.subject = "Physics"
        mock_exam.level = "bachelor"
        mock_exam.exam_type = "written"
        mock_exam.original_content = "Test content"
        mock_exam.cache_name = "original_cache"
        mock_exam_repo.get_by_id.return_value = mock_exam
        
        # Mock fallback to return updated cache name
        mock_fallback_service.execute_with_fallback.return_value = ({}, "updated_cache")
        
        # Execute
        result = await topic_generator.generate_batch(
            topic_ids=[topic_id],
            cache_name="original_cache",
            exam_id=exam_id
        )
        
        # Verify fallback was called
        mock_fallback_service.execute_with_fallback.assert_called_once()
        call_kwargs = mock_fallback_service.execute_with_fallback.call_args.kwargs
        assert call_kwargs["exam_id"] == exam_id
        assert call_kwargs["cache_name"] == "original_cache"

    @pytest.mark.asyncio
    async def test_generate_batch_state_transitions(
        self,
        topic_generator,
        mock_topic_repo,
        mock_exam_repo,
        mock_executor
    ):
        """Test that topics transition through correct states during generation"""
        # Setup
        exam_id = uuid4()
        topic_id = uuid4()
        
        mock_topic = Mock()
        mock_topic.id = topic_id
        mock_topic.exam_id = exam_id
        mock_topic.topic_name = "Test Topic"
        mock_topic.status = "pending"
        mock_topic.content = None
        mock_topic.user_id = uuid4()
        mock_topic.mark_as_ready = Mock()
        mock_topic_repo.get_by_id.return_value = mock_topic
        
        mock_exam = Mock()
        mock_exam.id = exam_id
        mock_exam.subject = "Physics"
        mock_exam.level = "bachelor"
        mock_exam.exam_type = "written"
        mock_exam.original_content = "Test content"
        mock_exam.cache_name = "test_cache"
        mock_exam_repo.get_by_id.return_value = mock_exam
        
        # Mock fallback service
        topic_generator.fallback.execute_with_fallback.return_value = (
            {str(topic_id): "Generated content for topic"}, 
            None
        )
        
        # Execute
        await topic_generator.generate_batch(
            topic_ids=[topic_id],
            exam_id=exam_id
        )
        
        # Verify topic was marked as ready
        mock_topic.mark_as_ready.assert_called_once_with("Generated content for topic")
        mock_topic_repo.update.assert_called_once_with(mock_topic)
