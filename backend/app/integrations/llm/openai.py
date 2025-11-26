import logging
import time
from typing import Any, Optional

from openai import AsyncOpenAI

from app.integrations.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation"""

    # Pricing (as of Nov 2024, verify on https://openai.com/pricing)
    PRICING = {
        "gpt-4o": {
            "input": 2.50 / 1_000_000,  # $2.50 per 1M tokens
            "output": 10.00 / 1_000_000,  # $10.00 per 1M tokens
        },
        "gpt-4o-mini": {
            "input": 0.150 / 1_000_000,  # $0.15 per 1M tokens
            "output": 0.600 / 1_000_000,  # $0.60 per 1M tokens
        },
        "gpt-4-turbo": {
            "input": 10.00 / 1_000_000,
            "output": 30.00 / 1_000_000,
        },
        "gpt-3.5-turbo": {
            "input": 0.50 / 1_000_000,
            "output": 1.50 / 1_000_000,
        },
    }

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.model_name = model

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        response_schema: Optional[Any] = None,
        **kwargs,
    ) -> LLMResponse:
        """Generate text with OpenAI"""

        start_time = time.time()

        try:
            # Build messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # Configure generation
            kwargs = {
                "model": self.model_name,
                "messages": messages,
                "temperature": temperature,
            }

            if max_tokens:
                kwargs["max_tokens"] = max_tokens

            # Add structured output if response_schema provided
            if response_schema:
                # OpenAI supports JSON mode
                kwargs["response_format"] = {"type": "json_object"}
                # Add instruction to system prompt
                if system_prompt:
                    messages[0]["content"] += "\n\nRespond with valid JSON only."
                else:
                    messages.insert(0, {"role": "system", "content": "Respond with valid JSON only."})

            print(f"[OpenAIProvider] Calling {self.model_name} API...")
            api_start = time.time()

            # Generate
            response = await self.client.chat.completions.create(**kwargs)

            api_time = time.time() - api_start
            total_time = time.time() - start_time

            # Extract usage stats
            usage = response.usage
            tokens_input = usage.prompt_tokens
            tokens_output = usage.completion_tokens

            print(
                f"[OpenAIProvider] API call: {api_time:.2f}s, Total: {total_time:.2f}s, Tokens: {tokens_input}/{tokens_output}"
            )

            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output)

            return LLMResponse(
                content=response.choices[0].message.content,
                model=self.model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason=response.choices[0].finish_reason,
            )

        except Exception as e:
            elapsed = time.time() - start_time
            print(
                f"[OpenAIProvider] ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}"
            )
            import traceback

            traceback.print_exc()
            raise RuntimeError(f"OpenAI API error: {str(e)}")

    async def count_tokens(self, text: str) -> int:
        """
        Count tokens using tiktoken (OpenAI's tokenizer).
        For simplicity, we'll use a rough estimate: ~4 chars per token.
        For production, install tiktoken and use proper tokenization.
        """
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4

    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD"""
        pricing = self.PRICING.get(self.model_name, self.PRICING["gpt-4o-mini"])

        input_cost = tokens_input * pricing["input"]
        output_cost = tokens_output * pricing["output"]

        return input_cost + output_cost
