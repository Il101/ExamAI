import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4
from app.services.cache_fallback import CacheFallbackService
from app.agent.cached_executor import CachedTopicExecutor
from app.agent.state import AgentState, PlanStep, Priority

@pytest.mark.asyncio
async def test_cached_executor_uses_fallback_on_403():
    """Verify that CachedTopicExecutor calls fallback_service on 403 error"""
    
    # Setup Mocks
    mock_llm = AsyncMock()
    mock_llm.client = Mock()
    mock_llm.client.aio = Mock()
    mock_llm.client.aio.models = Mock()
    mock_llm.client.aio.models.generate_content = AsyncMock()
    
    # Simulate 403 Permisson Denied
    mock_llm.client.aio.models.generate_content.side_effect = Exception("403 Forbidden: CachedContent not found")
    
    mock_fallback = AsyncMock(spec=CacheFallbackService)
    # Fallback should return content
    mock_fallback.execute_with_fallback.return_value = "Recovered Content"
    
    executor = CachedTopicExecutor(mock_llm, fallback_service=mock_fallback)
    
    # Setup State
    exam_id = uuid4()
    step = PlanStep(id=1, title="Test Topic", description="Test description for validation", priority=Priority.HIGH, estimated_paragraphs=1)
    state = AgentState(
        user_request="Test", 
        subject="Test", 
        exam_type="written",
        level="bachelor",
        exam_id=str(exam_id), 
        cache_name="expired_cache"
    )
    state.plan = [step]
    
    # Execute
    content = await executor.execute_step(state)
    
    # Verify
    assert content == "Recovered Content"
    
    # Check if fallback service was called correcty
    mock_fallback.execute_with_fallback.assert_called_once()
    
    # Verify args passed to fallback
    call_args = mock_fallback.execute_with_fallback.call_args
    assert call_args[0][0] == exam_id  # Exam ID
    assert call_args[0][1] == "expired_cache" # Old Cache Name
    # The 3rd arg is the generate_op callback 
    assert callable(call_args[0][2]) 

