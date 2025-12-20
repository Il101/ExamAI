"""
Unit tests for exam generation Celery tasks.

These tests ensure the exam generation pipeline works correctly and prevent
regression bugs like the recent TypeError with generate_batch() parameters.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, call
from uuid import uuid4

from app.tasks.exam_tasks import _generate_exam_content_async


class TestExamGenerationTasks:
    """Tests for exam generation Celery tasks"""

    @pytest.mark.asyncio
    async def test_generate_exam_content_async_batch_parameters(self, mocker):
        """
        CRITICAL TEST: Verify generate_batch is called with correct parameters.
        This test would have caught the recent bug where user_id was incorrectly passed.
        """
        # Setup mock data
        exam_id = uuid4()
        user_id = uuid4()
        topic_id = uuid4()
        
        # Mock repositories and their responses
        mock_user = Mock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.preferred_language = "en"
        
        mock_exam = Mock()
        mock_exam.id = exam_id
        mock_exam.status = "generating"
        mock_exam.cache_name = "test_cache"
        mock_exam.subject = "Physics"
        mock_exam.exam_type = "written"
        mock_exam.level = "bachelor"
        mock_exam.original_content = "Test content"
        mock_exam.title = "Test Exam"
        mock_exam.mark_as_ready = Mock()
        
        mock_topic = Mock()
        mock_topic.id = topic_id
        mock_topic.status = "pending"
        mock_topic.content = None
        mock_topic.topic_name = "Test Topic"
        mock_topic.exam_id = exam_id
        mock_topic.user_id = user_id
        
        # Mock repositories
        mock_user_repo = AsyncMock()
        mock_user_repo.get_by_id.return_value = mock_user
        
        mock_exam_repo = AsyncMock()
        mock_exam_repo.get_by_id.return_value = mock_exam
        mock_exam_repo.update = AsyncMock()
        
        mock_topic_repo = AsyncMock()
        mock_topic_repo.get_by_exam_id.return_value = [mock_topic]
        
        # Patch repository constructors
        mocker.patch("app.tasks.exam_tasks.UserRepository", return_value=mock_user_repo)
        mocker.patch("app.tasks.exam_tasks.ExamRepository", return_value=mock_exam_repo)
        mocker.patch("app.tasks.exam_tasks.TopicRepository", return_value=mock_topic_repo)
        mocker.patch("app.tasks.exam_tasks.ReviewItemRepository")
        
        # Mock TopicContentGenerator
        mock_topic_gen = AsyncMock()
        mock_topic_gen.generate_batch.return_value = {
            "results": {str(topic_id): {}},
            "usage": {"tokens_input": 1000, "tokens_output": 500, "cost_usd": 0.01}
        }
        mocker.patch(
            "app.tasks.exam_tasks.TopicContentGenerator",
            return_value=mock_topic_gen
        )
        
        # Mock other services
        mocker.patch("app.tasks.exam_tasks.TopicExecutor")
        mocker.patch("app.tasks.exam_tasks.QuizGenerator")
        mocker.patch("app.tasks.exam_tasks.FlashcardGenerator")
        mocker.patch("app.tasks.exam_tasks.SupabaseStorage")
        mocker.patch("app.tasks.exam_tasks.GeminiProvider")
        mocker.patch("app.tasks.exam_tasks.ContextCacheManager")
        mocker.patch("app.tasks.exam_tasks.CacheFallbackService")
        mock_summary_gen = AsyncMock()
        mock_summary_gen.generate_tldr.return_value = ("Summary", {"tokens_input": 0, "tokens_output": 0, "cost_usd": 0})
        mocker.patch("app.tasks.exam_tasks.ExamSummaryGenerator", return_value=mock_summary_gen)
        
        # Mock task
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute
        await _generate_exam_content_async(
            exam_id=exam_id,
            user_id=user_id,
            task=mock_task
        )
        
        # CRITICAL VERIFICATION: Check that generate_batch was called with correct parameters
        assert mock_topic_gen.generate_batch.called, "generate_batch should have been called"
        
        # Get the actual call arguments
        call_args = mock_topic_gen.generate_batch.call_args
        
        # Verify REQUIRED parameters are present
        assert "topic_ids" in call_args.kwargs, "topic_ids parameter is required"
        assert "cache_name" in call_args.kwargs, "cache_name parameter is required"
        assert "exam_id" in call_args.kwargs, "exam_id parameter is required"
        assert "output_language" in call_args.kwargs, "output_language parameter is required"
        
        # CRITICAL: Verify user_id is NOT passed (this is the bug we're preventing!)
        assert "user_id" not in call_args.kwargs, (
            "generate_batch() should NOT receive 'user_id' parameter! "
            "This was the bug that caused TypeError in production."
        )
        
        # Verify parameter values
        assert call_args.kwargs["cache_name"] == "test_cache"
        assert call_args.kwargs["exam_id"] == exam_id
        assert call_args.kwargs["output_language"] == "en"

    @pytest.mark.asyncio
    async def test_generate_exam_content_async_batching_logic(
        self,
        test_session,
        mocker
    ):
        """Test that topics are correctly batched (batch_size=4)"""
        from app.db.models.exam import ExamModel
        from app.db.models.topic import TopicModel
        from app.db.models.user import UserModel
        
        # Create user
        user = UserModel(
            id=uuid4(),
            email="test@example.com",
            full_name="Test User",
            hashed_password="hash",
            subscription_plan="free"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Create exam
        exam = ExamModel(
            id=uuid4(),
            user_id=user.id,
            title="Test Exam",
            subject="Physics",
            exam_type="written",
            level="bachelor",
            original_content="Test content " * 20,
            status="generating",
            cache_name="test_cache"
        )
        test_session.add(exam)
        await test_session.flush()
        
        # Create 10 topics to test batching (should create 3 batches: 4+4+2)
        topics = []
        for i in range(10):
            topic = TopicModel(
                id=uuid4(),
                exam_id=exam.id,
                user_id=user.id,
                topic_name=f"Topic {i+1}",
                order_index=i,
                status="pending"
            )
            test_session.add(topic)
            topics.append(topic)
        
        await test_session.commit()
        
        # Mock dependencies
        mock_topic_gen = AsyncMock()
        mock_topic_gen.generate_batch.return_value = {
            "results": {},
            "usage": {"tokens_input": 100, "tokens_output": 50, "cost_usd": 0.001}
        }
        
        mocker.patch(
            "app.tasks.exam_tasks.TopicContentGenerator",
            return_value=mock_topic_gen
        )
        mocker.patch("app.tasks.exam_tasks.TopicExecutor")
        mocker.patch("app.tasks.exam_tasks.QuizGenerator")
        mocker.patch("app.tasks.exam_tasks.FlashcardGenerator")
        mocker.patch("app.tasks.exam_tasks.SupabaseStorage")
        mocker.patch("app.tasks.exam_tasks.GeminiProvider")
        mocker.patch("app.tasks.exam_tasks.ContextCacheManager")
        mocker.patch("app.tasks.exam_tasks.CacheFallbackService")
        mocker.patch("app.tasks.exam_tasks.ExamSummaryGenerator")
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute
        await _generate_exam_content_async(
            exam_id=exam.id,
            user_id=user.id,
            task=mock_task
        )
        
        # Verify generate_batch was called 3 times (10 topics / batch_size 4 = 3 batches)
        assert mock_topic_gen.generate_batch.call_count == 3
        
        # Verify batch sizes: first batch=4, second batch=4, third batch=2
        calls = mock_topic_gen.generate_batch.call_args_list
        assert len(calls[0].kwargs["topic_ids"]) == 4
        assert len(calls[1].kwargs["topic_ids"]) == 4
        assert len(calls[2].kwargs["topic_ids"]) == 2

    @pytest.mark.asyncio
    async def test_generate_exam_content_async_error_handling(
        self,
        sample_exam_with_topics,
        mocker
    ):
        """Test that batch failures are handled gracefully"""
        exam_data = sample_exam_with_topics
        exam = exam_data["exam"]
        user = exam_data["user"]
        
        # Mock topic generator to raise an error
        mock_topic_gen = AsyncMock()
        mock_topic_gen.generate_batch.side_effect = Exception("API Error")
        
        mocker.patch(
            "app.tasks.exam_tasks.TopicContentGenerator",
            return_value=mock_topic_gen
        )
        mocker.patch("app.tasks.exam_tasks.TopicExecutor")
        mocker.patch("app.tasks.exam_tasks.QuizGenerator")
        mocker.patch("app.tasks.exam_tasks.FlashcardGenerator")
        mocker.patch("app.tasks.exam_tasks.SupabaseStorage")
        mocker.patch("app.tasks.exam_tasks.GeminiProvider")
        mocker.patch("app.tasks.exam_tasks.ContextCacheManager")
        mocker.patch("app.tasks.exam_tasks.CacheFallbackService")
        mocker.patch("app.tasks.exam_tasks.ExamSummaryGenerator")
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute - should not raise (errors should be handled)
        result = await _generate_exam_content_async(
            exam_id=exam.id,
            user_id=user.id,
            task=mock_task
        )
        
        # Verify task still completes with partial success
        assert result["status"] == "success"
        assert result["ready_topics"] == 0  # No topics succeeded

    @pytest.mark.asyncio
    async def test_generate_exam_content_async_usage_aggregation(
        self,
        sample_exam_with_topics,
        mocker
    ):
        """Test that token usage and costs are correctly aggregated across batches"""
        exam_data = sample_exam_with_topics
        exam = exam_data["exam"]
        user = exam_data["user"]
        
        # Mock topic generator with different usage per batch
        mock_topic_gen = AsyncMock()
        mock_topic_gen.generate_batch.side_effect = [
            {"results": {}, "usage": {"tokens_input": 1000, "tokens_output": 500, "cost_usd": 0.01}},
            {"results": {}, "usage": {"tokens_input": 1500, "tokens_output": 750, "cost_usd": 0.015}},
        ]
        
        mocker.patch(
            "app.tasks.exam_tasks.TopicContentGenerator",
            return_value=mock_topic_gen
        )
        mocker.patch("app.tasks.exam_tasks.TopicExecutor")
        mocker.patch("app.tasks.exam_tasks.QuizGenerator")
        mocker.patch("app.tasks.exam_tasks.FlashcardGenerator")
        mocker.patch("app.tasks.exam_tasks.SupabaseStorage")
        mocker.patch("app.tasks.exam_tasks.GeminiProvider")
        mocker.patch("app.tasks.exam_tasks.ContextCacheManager")
        mocker.patch("app.tasks.exam_tasks.CacheFallbackService")
        
        # Mock summary generator
        mock_summary_gen = AsyncMock()
        mock_summary_gen.generate_tldr.return_value = (
            "Test summary",
            {"tokens_input": 500, "tokens_output": 100, "cost_usd": 0.005}
        )
        mocker.patch(
            "app.tasks.exam_tasks.ExamSummaryGenerator",
            return_value=mock_summary_gen
        )
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute
        await _generate_exam_content_async(
            exam_id=exam.id,
            user_id=user.id,
            task=mock_task
        )
        
        # Refresh exam from database
        await test_session.refresh(exam)
        
        # Verify aggregated usage (2 batches + summary)
        # Total input: 1000 + 1500 + 500 = 3000
        # Total output: 500 + 750 + 100 = 1350
        # Total cost: 0.01 + 0.015 + 0.005 = 0.03
        assert exam.token_input == 3000
        assert exam.token_output == 1350
        assert exam.cost == pytest.approx(0.03, abs=0.001)

    @pytest.mark.asyncio
    async def test_generate_exam_content_async_notifications(
        self,
        sample_exam_with_topics,
        mocker
    ):
        """Test that notifications are triggered after successful generation"""
        exam_data = sample_exam_with_topics
        exam = exam_data["exam"]
        user = exam_data["user"]
        user.notification_exam_ready = True
        
        # Mock dependencies
        mock_topic_gen = AsyncMock()
        mock_topic_gen.generate_batch.return_value = {
            "results": {},
            "usage": {"tokens_input": 100, "tokens_output": 50, "cost_usd": 0.001}
        }
        
        mocker.patch(
            "app.tasks.exam_tasks.TopicContentGenerator",
            return_value=mock_topic_gen
        )
        mocker.patch("app.tasks.exam_tasks.TopicExecutor")
        mocker.patch("app.tasks.exam_tasks.QuizGenerator")
        mocker.patch("app.tasks.exam_tasks.FlashcardGenerator")
        mocker.patch("app.tasks.exam_tasks.SupabaseStorage")
        mocker.patch("app.tasks.exam_tasks.GeminiProvider")
        mocker.patch("app.tasks.exam_tasks.ContextCacheManager")
        mocker.patch("app.tasks.exam_tasks.CacheFallbackService")
        mocker.patch("app.tasks.exam_tasks.ExamSummaryGenerator")
        
        # Mock notification tasks
        mock_email_notification = mocker.patch("app.tasks.email_tasks.send_exam_ready_notification")
        mock_email_notification.delay = Mock()
        
        mock_push_notification = mocker.patch("app.tasks.email_tasks.send_user_push_notification")
        mock_push_notification.delay = Mock()
        
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        # Execute
        await _generate_exam_content_async(
            exam_id=exam.id,
            user_id=user.id,
            task=mock_task
        )
        
        # Verify notifications were triggered
        mock_email_notification.delay.assert_called_once()
        mock_push_notification.delay.assert_called_once()
        
        # Verify notification parameters
        email_call = mock_email_notification.delay.call_args
        assert email_call.kwargs["user_email"] == user.email
        assert email_call.kwargs["exam_title"] == exam.title
        
        push_call = mock_push_notification.delay.call_args
        assert push_call.kwargs["user_id"] == str(user.id)
        assert "ready" in push_call.kwargs["title"].lower()
