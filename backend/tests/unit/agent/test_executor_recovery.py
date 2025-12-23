import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from app.agent.executor import TopicExecutor
from app.agent.state import AgentState, PlanStep, Priority

@pytest.mark.asyncio
async def test_execute_all_steps_partial_batch_recovery():
    """
    Test that execute_all_steps_with_recovery does not skip topics
    when a batch returns partial results (e.g. skips a middle topic).
    """
    # 1. Setup mock LLM and Executor
    llm = MagicMock()
    executor = TopicExecutor(llm)
    
    # 2. Setup state with 4 topics
    topic_ids = [uuid4() for _ in range(4)]
    state = AgentState(
        user_request="Test",
        subject="Test",
        level="Test",
        exam_type="Test",
        original_content="Test"
    )
    state.plan = [
        PlanStep(id=tid, title=f"Topic {i}", description=f"Description for topic {i}", priority=Priority.MEDIUM)
        for i, tid in enumerate(topic_ids)
    ]
    
    # 3. Mock execute_batch to fail partially on first call
    # Batch 1 (4 topics): Returns 0, 1, 3 (skips index 2)
    first_batch_results = {
        str(topic_ids[0]): "Content 0",
        str(topic_ids[1]): "Content 1",
        str(topic_ids[3]): "Content 3",
    }
    
    # Subsequent calls (individual or smaller batches)
    # After fix: index 2 should be retried
    second_call_results = {
        str(topic_ids[2]): "Content 2"
    }
    third_call_results = {
        str(topic_ids[3]): "Content 3"
    }
    
    executor.execute_batch = AsyncMock()
    executor.execute_batch.side_effect = [
        first_batch_results, # Call 1
        second_call_results, # Call 2
        third_call_results   # Call 3
    ]
    
    # Mock execute_step just in case it falls back to individual
    executor.execute_step = AsyncMock(return_value="Individual Content")
    
    # 4. Run recovery-aware execution with initial batch size 4
    results = await executor.execute_all_steps_with_recovery(state, initial_batch_size=4)
    
    # 5. Assertions
    # Total topics should be 4
    assert len(results) == 4
    for tid in topic_ids:
        assert str(tid) in results
        assert results[str(tid)].success is True
    
    # Check that it advanced correctly
    # Call 1: got 0, 1. Counted consecutive=2. remaining becomes [2, 3]
    # Call 2: got 2. Counted consecutive=1. remaining becomes [3]
    # Call 3: got 3. Counted consecutive=1. remaining becomes []
    assert executor.execute_batch.call_count >= 3
    
    # Verify that the second call was for topic 2
    actual_call_args = executor.execute_batch.call_args_list
    # First call: topics [0, 1, 2, 3]
    assert [s.id for s in actual_call_args[0][0][1]] == topic_ids
    # Second call: topics [2, 3] (since batch size resets or stays)
    assert topic_ids[2] in [s.id for s in actual_call_args[1][0][1]]
    assert topic_ids[0] not in [s.id for s in actual_call_args[1][0][1]]
