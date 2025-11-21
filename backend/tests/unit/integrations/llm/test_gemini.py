import pytest
from unittest.mock import AsyncMock, Mock, patch
import time

from app.integrations.llm.gemini import GeminiProvider
from app.integrations.llm.base import LLMResponse

@pytest.fixture
def mock_genai():
    with patch("app.integrations.llm.gemini.genai") as mock:
        yield mock

@pytest.fixture
def gemini_provider(mock_genai):
    return GeminiProvider(api_key="key", model="gemini-2.0-flash-exp")

@pytest.mark.asyncio
async def test_generate_success(gemini_provider, mock_genai):
    """Test successful generation"""
    prompt = "Hello"
    mock_response = Mock()
    mock_response.text = "Hello there!"
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.candidates_token_count = 20

    mock_candidate = Mock()
    mock_candidate.finish_reason.name = "STOP"
    mock_response.candidates = [mock_candidate]

    # Mock generate_content_async on the model instance created in __init__
    gemini_provider.model.generate_content_async = AsyncMock(return_value=mock_response)

    response = await gemini_provider.generate(prompt)

    assert isinstance(response, LLMResponse)
    assert response.content == "Hello there!"
    assert response.tokens_input == 10
    assert response.tokens_output == 20
    assert response.finish_reason == "stop"

    gemini_provider.model.generate_content_async.assert_called_once()
    args, kwargs = gemini_provider.model.generate_content_async.call_args
    assert args[0] == prompt
    # In mocks, kwargs values are often other Mocks unless configured otherwise.
    # However, we are checking what was passed to generate_content_async.
    # The code does: generation_config = genai.GenerationConfig(temperature=temperature...)
    # The mock_genai.GenerationConfig is a mock class.
    # So we should check if GenerationConfig was called with correct params,
    # OR check the attributes of the config object passed if it's a real object.
    # Since genai is mocked, GenerationConfig returns a Mock.

    # Let's verify GenerationConfig was instantiated with correct params
    mock_genai.GenerationConfig.assert_called_with(
        temperature=0.7,
        max_output_tokens=None
    )

@pytest.mark.asyncio
async def test_generate_with_system_prompt(gemini_provider, mock_genai):
    """Test generation with system prompt"""
    prompt = "User prompt"
    system_prompt = "System prompt"

    mock_response = Mock()
    mock_response.text = "Response"
    mock_response.usage_metadata.prompt_token_count = 5
    mock_response.usage_metadata.candidates_token_count = 5

    mock_candidate = Mock()
    mock_candidate.finish_reason.name = "STOP"
    mock_response.candidates = [mock_candidate]

    gemini_provider.model.generate_content_async = AsyncMock(return_value=mock_response)

    await gemini_provider.generate(prompt, system_prompt=system_prompt)

    args, _ = gemini_provider.model.generate_content_async.call_args
    assert "System prompt" in args[0]
    assert "User prompt" in args[0]

@pytest.mark.asyncio
async def test_generate_with_schema(gemini_provider, mock_genai):
    """Test generation with response schema"""
    schema = {"type": "object"}

    mock_response = Mock()
    mock_response.text = "{}"
    mock_response.usage_metadata.prompt_token_count = 5
    mock_response.usage_metadata.candidates_token_count = 5

    mock_candidate = Mock()
    mock_candidate.finish_reason.name = "STOP"
    mock_response.candidates = [mock_candidate]

    gemini_provider.model.generate_content_async = AsyncMock(return_value=mock_response)

    await gemini_provider.generate("prompt", response_schema=schema)

    # Verify the config object passed has the attributes set
    # Since GenerationConfig returns a Mock, we can check if attributes were set on it.
    # The code does:
    # generation_config.response_mime_type = "application/json"
    # generation_config.response_schema = response_schema

    # We can retrieve the return value of GenerationConfig()
    config_mock = mock_genai.GenerationConfig.return_value
    assert config_mock.response_mime_type == "application/json"
    assert config_mock.response_schema == schema

@pytest.mark.asyncio
async def test_generate_failure(gemini_provider, mock_genai):
    """Test generation failure"""
    gemini_provider.model.generate_content_async = AsyncMock(side_effect=Exception("API Error"))

    with pytest.raises(RuntimeError, match="Gemini API error"):
        await gemini_provider.generate("prompt")

@pytest.mark.asyncio
async def test_count_tokens(gemini_provider, mock_genai):
    """Test token counting"""
    mock_result = Mock()
    mock_result.total_tokens = 100
    gemini_provider.model.count_tokens_async = AsyncMock(return_value=mock_result)

    count = await gemini_provider.count_tokens("text")
    assert count == 100

def test_calculate_cost(gemini_provider):
    """Test cost calculation"""
    # gemini-2.0-flash-exp is 0/0 currently in the class
    cost = gemini_provider.calculate_cost(1000, 1000)
    assert cost == 0.0

    # Test with paid model
    gemini_provider.model_name = "gemini-1.5-flash"
    # input: 0.075 / 1M -> 1000 tokens = 0.000075
    # output: 0.30 / 1M -> 1000 tokens = 0.00030
    # total: 0.000375
    cost = gemini_provider.calculate_cost(1000, 1000)
    assert abs(cost - 0.000375) < 1e-9
