import google.generativeai as genai
from typing import Optional, Any
import time
import logging
from app.integrations.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation"""
    
    # Pricing (as of Nov 2024, verify on https://ai.google.dev/pricing)
    PRICING = {
        "gemini-2.0-flash-exp": {
            "input": 0.00 / 1_000_000,   # Free tier
            "output": 0.00 / 1_000_000,
        },
        "gemini-1.5-flash": {
            "input": 0.075 / 1_000_000,   # $0.075 per 1M tokens
            "output": 0.30 / 1_000_000,   # $0.30 per 1M tokens
        },
        "gemini-1.5-pro": {
            "input": 1.25 / 1_000_000,
            "output": 5.00 / 1_000_000,
        }
    }
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini provider.
        
        Args:
            api_key: Gemini API key
            model: Model name (gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro)
        """
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(model)
    
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        response_schema: Optional[Any] = None,
    ) -> LLMResponse:
        """Generate text with Gemini"""
        
        start_time = time.time()
        
        try:
            # Combine system prompt with user prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            # Configure generation
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            
            # Add response schema if provided (Gemini 1.5 Pro/Flash feature)
            if response_schema:
                generation_config.response_mime_type = "application/json"
                generation_config.response_schema = response_schema
            
            print(f"[GeminiProvider] Calling {self.model_name} API...")
            api_start = time.time()
            # Generate
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config
            )
            api_time = time.time() - api_start
            total_time = time.time() - start_time
            
            # Extract usage stats
            usage = response.usage_metadata
            tokens_input = usage.prompt_token_count
            tokens_output = usage.candidates_token_count
            
            print(f"[GeminiProvider] API call: {api_time:.2f}s, Total: {total_time:.2f}s, Tokens: {tokens_input}/{tokens_output}")
            
            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output)
            
            return LLMResponse(
                content=response.text,
                model=self.model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason=response.candidates[0].finish_reason.name.lower()
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            # Log error and re-raise
            print(f"[GeminiProvider] ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Gemini API error: {str(e)}")
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's tokenizer"""
        result = await self.model.count_tokens_async(text)
        return result.total_tokens
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name
    
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD"""
        pricing = self.PRICING.get(self.model_name, self.PRICING["gemini-2.0-flash-exp"])
        
        input_cost = tokens_input * pricing["input"]
        output_cost = tokens_output * pricing["output"]
        
        return input_cost + output_cost
