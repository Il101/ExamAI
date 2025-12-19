"""
LLM Fallback Wrapper - automatically switches to fallback model on 503 errors
"""
import logging
from typing import Any, Optional

from app.integrations.llm.base import LLMProvider, LLMResponse
from app.integrations.llm.gemini import GeminiProvider

from app.core.config import settings

logger = logging.getLogger(__name__)


class FallbackLLMProvider(LLMProvider):
    """
    Wrapper that automatically falls back to a secondary model on 503/overload errors.
    
    Usage:
        primary = GeminiProvider(api_key, model=settings.GEMINI_MODEL)
        fallback = GeminiProvider(api_key, model=settings.GEMINI_FALLBACK_MODEL)
        llm = FallbackLLMProvider(primary, fallback)
    """
    
    def __init__(
        self, 
        primary: LLMProvider, 
        fallback: LLMProvider,
        fallback_on_codes: list[int] = [503]
    ):
        """
        Initialize fallback wrapper.
        
        Args:
            primary: Primary LLM provider to use first
            fallback: Fallback LLM provider to use on errors
            fallback_on_codes: List of HTTP error codes that trigger fallback
        """
        self.primary = primary
        self.fallback = fallback
        self.fallback_on_codes = fallback_on_codes
        self._fallback_used = False
        
    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        response_schema: Optional[Any] = None,
        response_mime_type: Optional[str] = None,
        timeout: float = 180.0,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate with automatic fallback on 503 errors.
        """
        try:
            # Try primary model first
            logger.info(f"[FallbackLLM] Trying primary model: {self.primary.get_model_name()}")
            return await self.primary.generate(
                prompt=prompt,
                temperature=temperature,
                max_tokens=max_tokens,
                system_prompt=system_prompt,
                response_schema=response_schema,
                response_mime_type=response_mime_type,
                timeout=timeout,
                **kwargs
            )
            
        except RuntimeError as e:
            error_msg = str(e)
            
            # Check if error code matches fallback triggers
            should_fallback = any(
                str(code) in error_msg 
                for code in self.fallback_on_codes
            )
            
            if should_fallback:
                logger.warning(
                    f"[FallbackLLM] Primary model failed with {error_msg}. "
                    f"Switching to fallback: {self.fallback.get_model_name()}"
                )
                self._fallback_used = True
                
                # Retry with fallback model
                return await self.fallback.generate(
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    system_prompt=system_prompt,
                    response_schema=response_schema,
                    response_mime_type=response_mime_type,
                    timeout=timeout,
                    **kwargs
                )
            else:
                # Non-fallback error, re-raise
                raise
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens using primary model's tokenizer"""
        return await self.primary.count_tokens(text)
    
    def get_model_name(self) -> str:
        """Get current model name (includes fallback if used)"""
        if self._fallback_used:
            return f"{self.primary.get_model_name()} -> {self.fallback.get_model_name()}"
        return self.primary.get_model_name()
    
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost based on which model was actually used"""
        if self._fallback_used:
            return self.fallback.calculate_cost(tokens_input, tokens_output)
        return self.primary.calculate_cost(tokens_input, tokens_output)
    
    def reset_fallback_state(self):
        """Reset fallback tracking (call between separate requests)"""
        self._fallback_used = False
    
    @property
    def client(self):
        """Expose the primary provider's client for compatibility"""
        return self.primary.client
