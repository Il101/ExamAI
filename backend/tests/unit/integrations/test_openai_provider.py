"""
Tests for OpenAI LLM provider.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from app.integrations.llm.openai import OpenAIProvider
from app.integrations.llm.base import LLMResponse


@pytest.fixture
def openai_provider():
    """Create OpenAI provider instance for testing"""
    return OpenAIProvider(api_key="test-key", model="gpt-4o-mini")


def test_openai_provider_initialization():
    """Test OpenAI provider initialization"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
    assert provider.model_name == "gpt-4o"
    assert provider.client is not None


def test_get_model_name(openai_provider):
    """Test get_model_name method"""
    assert openai_provider.get_model_name() == "gpt-4o-mini"


def test_calculate_cost_gpt4o_mini(openai_provider):
    """Test cost calculation for GPT-4o-mini"""
    cost = openai_provider.calculate_cost(tokens_input=1000, tokens_output=500)
    
    # Expected: (1000 * 0.150/1M) + (500 * 0.600/1M)
    expected = (1000 * 0.150 / 1_000_000) + (500 * 0.600 / 1_000_000)
    assert cost == pytest.approx(expected)


def test_calculate_cost_gpt4o():
    """Test cost calculation for GPT-4o"""
    provider = OpenAIProvider(api_key="test-key", model="gpt-4o")
    cost = provider.calculate_cost(tokens_input=1000, tokens_output=500)
    
    # Expected: (1000 * 2.50/1M) + (500 * 10.00/1M)
    expected = (1000 * 2.50 / 1_000_000) + (500 * 10.00 / 1_000_000)
    assert cost == pytest.approx(expected)


@pytest.mark.asyncio
async def test_count_tokens(openai_provider):
    """Test token counting (rough estimate)"""
    text = "This is a test message with some words"
    tokens = await openai_provider.count_tokens(text)
    
    # Should be roughly len(text) / 4
    expected = len(text) // 4
    assert tokens == expected


@pytest.mark.asyncio
async def test_generate_success(openai_provider):
    """Test successful text generation"""
    # Mock the OpenAI client
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Generated text"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
    
    with patch.object(
        openai_provider.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ):
        result = await openai_provider.generate(
            prompt="Test prompt",
            temperature=0.7,
        )
        
        assert isinstance(result, LLMResponse)
        assert result.content == "Generated text"
        assert result.model == "gpt-4o-mini"
        assert result.tokens_input == 10
        assert result.tokens_output == 20
        assert result.finish_reason == "stop"
        assert result.cost_usd > 0


@pytest.mark.asyncio
async def test_generate_with_system_prompt(openai_provider):
    """Test generation with system prompt"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Response"
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 15
    mock_response.usage.completion_tokens = 10
    
    with patch.object(
        openai_provider.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ) as mock_create:
        await openai_provider.generate(
            prompt="User prompt",
            system_prompt="System instructions",
        )
        
        # Verify system prompt was included
        call_args = mock_create.call_args
        messages = call_args.kwargs['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[0]['content'] == 'System instructions'
        assert messages[1]['role'] == 'user'


@pytest.mark.asyncio
async def test_generate_with_json_mode(openai_provider):
    """Test generation with JSON response format"""
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = '{"key": "value"}'
    mock_response.choices[0].finish_reason = "stop"
    mock_response.usage = Mock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 5
    
    with patch.object(
        openai_provider.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        return_value=mock_response
    ) as mock_create:
        await openai_provider.generate(
            prompt="Generate JSON",
            response_schema={"type": "object"},
        )
        
        # Verify JSON mode was enabled
        call_args = mock_create.call_args
        assert call_args.kwargs['response_format'] == {"type": "json_object"}


@pytest.mark.asyncio
async def test_generate_error_handling(openai_provider):
    """Test error handling in generate method"""
    with patch.object(
        openai_provider.client.chat.completions,
        'create',
        new_callable=AsyncMock,
        side_effect=Exception("API Error")
    ):
        with pytest.raises(RuntimeError, match="OpenAI API error"):
            await openai_provider.generate(prompt="Test")
