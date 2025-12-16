"""
Unit tests for ExamSummaryGenerator truncation handling.

Tests verify that the summary generator:
1. Detects truncated responses via finish_reason
2. Retries with doubled token limit (4000)
3. Falls back to status message on double truncation
4. Returns complete summaries on successful generation
"""

import pytest
from unittest.mock import AsyncMock
from app.services.content_generation.summary_generator import (
    ExamSummaryGenerator,
    TopicGist,
)
from app.integrations.llm.base import LLMResponse


@pytest.mark.asyncio
async def test_generate_tldr_handles_truncation():
    """Test that generate_tldr retries when response is truncated"""

    # Mock LLM provider
    mock_llm = AsyncMock()

    # First call returns truncated response
    truncated_response = LLMResponse(
        content="- Topic 1: Some content\n- Topic 2: Incomplete conte",
        model="gemini-2.0-flash",
        tokens_input=100,
        tokens_output=2000,
        cost_usd=0.01,
        finish_reason="max_output_tokens",  # Indicates truncation
    )

    # Second call (retry) returns complete response
    complete_response = LLMResponse(
        content="- Topic 1: Some content\n- Topic 2: Complete content here\n- Topic 3: More content",
        model="gemini-2.0-flash",
        tokens_input=100,
        tokens_output=1500,
        cost_usd=0.01,
        finish_reason="stop",  # Normal completion
    )

    # Configure mock to return different responses on consecutive calls
    mock_llm.generate.side_effect = [truncated_response, complete_response]

    # Create generator and call generate_tldr
    generator = ExamSummaryGenerator(mock_llm)
    result = await generator.generate_tldr(
        subject="Test Subject",
        exam_type="written",
        level="bachelor",
        topics=[TopicGist(title="Topic 1", content="Content 1")],
        total_count=3,
        ready_count=3,
    )

    # Assertions
    assert "Complete content" in result
    assert mock_llm.generate.call_count == 2  # Called twice (initial + retry)

    # Verify max_tokens increased on retry
    first_call = mock_llm.generate.call_args_list[0]
    second_call = mock_llm.generate.call_args_list[1]
    assert first_call[1]["max_tokens"] == 2000
    assert second_call[1]["max_tokens"] == 4000


@pytest.mark.asyncio
async def test_generate_tldr_fallback_on_double_truncation():
    """Test fallback message when both attempts are truncated"""

    # Mock LLM provider that always returns truncated responses
    mock_llm = AsyncMock()
    truncated_response = LLMResponse(
        content="- Incomplete",
        model="gemini-2.0-flash",
        tokens_input=100,
        tokens_output=2000,
        cost_usd=0.01,
        finish_reason="length",
    )
    mock_llm.generate.return_value = truncated_response

    generator = ExamSummaryGenerator(mock_llm)
    result = await generator.generate_tldr(
        subject="Математика",
        exam_type="written",
        level="bachelor",
        topics=[TopicGist(title="Topic 1", content="Content 1")],
        total_count=5,
        ready_count=3,
    )

    # Should return fallback message
    assert "Сгенерировано 3/5" in result
    assert "Математика" in result
    assert mock_llm.generate.call_count == 2  # Initial + 1 retry


@pytest.mark.asyncio
async def test_generate_tldr_normal_completion():
    """Test that normal responses (not truncated) work correctly"""

    # Mock LLM provider with normal response
    mock_llm = AsyncMock()
    normal_response = LLMResponse(
        content="- Topic 1: Complete summary\n- Topic 2: Another complete summary\n- Topic 3: Final summary",
        model="gemini-2.0-flash",
        tokens_input=100,
        tokens_output=500,
        cost_usd=0.005,
        finish_reason="stop",  # Normal completion
    )
    mock_llm.generate.return_value = normal_response

    generator = ExamSummaryGenerator(mock_llm)
    result = await generator.generate_tldr(
        subject="Physics",
        exam_type="oral",
        level="master",
        topics=[
            TopicGist(title="Topic 1", content="Content 1"),
            TopicGist(title="Topic 2", content="Content 2"),
        ],
        total_count=2,
        ready_count=2,
    )

    # Should return the normalized content
    assert "Complete summary" in result
    assert result.count("-") >= 3  # At least 3 bullet points
    assert mock_llm.generate.call_count == 1  # Only called once (no retry)


@pytest.mark.asyncio
async def test_generate_tldr_handles_different_finish_reasons():
    """Test that all truncation finish_reasons are handled"""

    test_cases = [
        ("max_tokens", True),  # Should trigger retry
        ("length", True),  # Should trigger retry
        ("max_output_tokens", True),  # Should trigger retry
        ("stop", False),  # Should NOT trigger retry
        ("", False),  # Empty finish_reason should NOT trigger retry
        (None, False),  # None finish_reason should NOT trigger retry
    ]

    for finish_reason, should_retry in test_cases:
        mock_llm = AsyncMock()

        first_response = LLMResponse(
            content="- Some content",
            model="gemini-2.0-flash",
            tokens_input=100,
            tokens_output=1000,
            cost_usd=0.01,
            finish_reason=finish_reason,
        )

        complete_response = LLMResponse(
            content="- Complete content after retry",
            model="gemini-2.0-flash",
            tokens_input=100,
            tokens_output=1000,
            cost_usd=0.01,
            finish_reason="stop",
        )

        if should_retry:
            mock_llm.generate.side_effect = [first_response, complete_response]
        else:
            mock_llm.generate.return_value = first_response

        generator = ExamSummaryGenerator(mock_llm)
        result = await generator.generate_tldr(
            subject="Test",
            exam_type="written",
            level="bachelor",
            topics=[TopicGist(title="Topic 1", content="Content 1")],
            total_count=1,
            ready_count=1,
        )

        # Verify retry behavior
        if should_retry:
            assert mock_llm.generate.call_count == 2, f"Failed for finish_reason={finish_reason}"
            assert "Complete content after retry" in result or "Сгенерировано" in result
        else:
            assert mock_llm.generate.call_count == 1, f"Failed for finish_reason={finish_reason}"
            assert "Some content" in result or result.strip() != ""
