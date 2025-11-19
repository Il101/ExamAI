"""Deterministic LLM responses for testing"""

import pytest

MOCK_COURSE_PLAN = {
    "plan": [
        {
            "topic_title": "Introduction to Calculus",
            "priority": 1,
            "dependencies": [],
            "estimated_paragraphs": 5,
        },
        {
            "topic_title": "Limits and Continuity",
            "priority": 2,
            "dependencies": [1],
            "estimated_paragraphs": 6,
        },
    ]
}

MOCK_TOPIC_CONTENT = """
# Introduction to Calculus

Calculus is the mathematical study of continuous change...

## Key Concepts
- Derivatives measure rate of change
- Integrals measure accumulation

## Examples
Example 1: Find derivative of f(x) = x²
Solution: f'(x) = 2x
"""


@pytest.fixture
def mock_gemini_provider(mocker):
    """Mock Gemini provider for tests"""
    mock_llm = mocker.Mock()

    mock_llm.generate_json.return_value = MOCK_COURSE_PLAN
    mock_llm.generate_text.return_value = MOCK_TOPIC_CONTENT
    mock_llm.count_tokens.return_value = 100
    mock_llm.calculate_cost.return_value = 0.05

    return mock_llm
