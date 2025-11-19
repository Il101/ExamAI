from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class LLMResponse:
    """Standardized LLM response"""

    content: str
    model: str
    tokens_input: int
    tokens_output: int
    cost_usd: float
    finish_reason: str  # "stop", "length", "error"

    @property
    def total_tokens(self) -> int:
        return self.tokens_input + self.tokens_output


@dataclass
class LLMUsage:
    """Token usage statistics"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    Allows switching between Gemini, OpenAI, Anthropic without changing business logic.
    """

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        response_schema: Optional[Any] = None,
    ) -> LLMResponse:
        """
        Generate text completion.

        Args:
            prompt: User prompt
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: System instructions
            response_schema: Optional schema for structured output (e.g. Pydantic model or list of models)

        Returns:
            LLMResponse with content and usage stats
        """

    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text for cost estimation"""

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""

    @abstractmethod
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD based on token usage"""
