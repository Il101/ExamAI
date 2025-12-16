import asyncio
import logging
import time
from typing import Any, Optional, List, Dict, Callable

from google import genai
from google.genai import types, errors

from app.integrations.llm.base import LLMProvider, LLMResponse
from app.integrations.llm.metrics import get_metrics

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation using google-genai SDK"""

    # Pricing (as of January 2025, verify on https://ai.google.dev/pricing)
    PRICING = {
        # Gemini 3.0 Series (Preview)
        "gemini-3-pro-preview": {
            "input": 2.00 / 1_000_000,   # $2.00 per 1M tokens (≤200K context)
            "output": 12.00 / 1_000_000,  # $12.00 per 1M tokens (≤200K context)
        },
        
        # Gemini 2.5 Series
        "gemini-2.5-pro": {
            "input": 1.25 / 1_000_000,   # $1.25 per 1M tokens
            "output": 10.00 / 1_000_000,  # $10.00 per 1M tokens
        },
        "gemini-2.5-flash": {
            "input": 0.30 / 1_000_000,   # $0.30 per 1M tokens
            "output": 2.50 / 1_000_000,  # $2.50 per 1M tokens
        },
        "gemini-2.5-flash-lite": {
            "input": 0.10 / 1_000_000,   # $0.10 per 1M tokens
            "output": 0.40 / 1_000_000,  # $0.40 per 1M tokens
        },
        
        # Gemini 2.0 Series
        "gemini-2.0-flash": {
            "input": 0.10 / 1_000_000,   # $0.10 per 1M tokens
            "output": 0.40 / 1_000_000,  # $0.40 per 1M tokens
        },
        "gemini-2.0-flash-exp": {
            "input": 0.00 / 1_000_000,   # FREE (experimental)
            "output": 0.00 / 1_000_000,  # FREE (experimental)
        },
        "gemini-2.0-flash-lite": {
            "input": 0.075 / 1_000_000,  # $0.075 per 1M tokens
            "output": 0.30 / 1_000_000,  # $0.30 per 1M tokens
        },
        
        # Gemini 1.5 Series (Legacy)
        "gemini-1.5-pro": {
            "input": 1.25 / 1_000_000,   # $1.25 per 1M tokens
            "output": 5.00 / 1_000_000,  # $5.00 per 1M tokens
        },
        "gemini-1.5-flash": {
            "input": 0.075 / 1_000_000,  # $0.075 per 1M tokens
            "output": 0.30 / 1_000_000,  # $0.30 per 1M tokens
        },
    }

    # Shared client instance for Singleton pattern
    _shared_client: Optional[genai.Client] = None
    _shared_api_key: Optional[str] = None

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini provider.
        
        Uses a shared client instance to enable connection pooling and efficient resource usage.
        Configures automatic retries for transient errors (429, 503).

        Args:
            api_key: Gemini API key
            model: Model name (gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro)
        """
        self.model_name = model
        self.client = self._get_client(api_key)

    @classmethod
    def _get_client(cls, api_key: str) -> genai.Client:
        """
        Get or create a shared genai.Client instance.
        """
        if cls._shared_client is None or cls._shared_api_key != api_key:
            # Configure timeout and retries using proper types.HttpOptions
            # IMPORTANT: Reduced retry attempts to 2 (from 5) to prevent conflicts
            # with our application-level retry mechanism in executor.py
            http_options = types.HttpOptions(
                timeout=240000,  # 240 seconds - must be > highest gen timeout (180s)
                retry_options={
                    "attempts": 2,  # Reduced from 5 to prevent retry cascade
                    "initial_delay": 1.0,
                    "max_delay": 10.0,  # Reduced from 60s
                    "exp_base": 2.0,
                    "http_status_codes": [429, 503],
                },
            )
            
            print(f"[GeminiProvider] Initializing new shared client with timeout=240s and 2 SDK retries...")
            cls._shared_client = genai.Client(api_key=api_key, http_options=http_options)
            cls._shared_api_key = api_key
            
        return cls._shared_client

    async def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        response_schema: Optional[Any] = None,
        response_mime_type: Optional[str] = None,
        timeout: float = 180.0,  # Increased timeout to 3 minutes
        **kwargs,
    ) -> LLMResponse:
        """Generate text with Gemini"""

        start_time = time.time()

        try:
            # Combine system prompt with user prompt
            # Note: new SDK supports system_instruction in config, but appending is safer for compatibility
            full_prompt = prompt
            
            config_args = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            if system_prompt:
                # If using cache, we CANNOT use system_instruction in config (API restriction)
                # So we must prepend it to the prompt contents
                if "cache_name" in kwargs and kwargs["cache_name"]:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                else:
                    config_args["system_instruction"] = system_prompt

            # Add cache support (CRITICAL for reducing input tokens)
            if "cache_name" in kwargs and kwargs["cache_name"]:
                config_args["cached_content"] = kwargs["cache_name"]
                print(f"[GeminiProvider] Using context cache: {kwargs['cache_name']}")

            # Add response schema if provided
            if response_schema:
                config_args["response_mime_type"] = "application/json"
                config_args["response_schema"] = response_schema
            elif response_mime_type:
                config_args["response_mime_type"] = response_mime_type

            config = types.GenerateContentConfig(**config_args)

            print(f"[GeminiProvider] Calling {self.model_name} API with timeout={timeout}s...")
            api_start = time.time()
            
            # Wrap in asyncio.wait_for for guaranteed timeout
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=full_prompt,
                    config=config
                ),
                timeout=timeout
            )
            
            api_time = time.time() - api_start
            total_time = time.time() - start_time

            # Extract usage stats
            usage = response.usage_metadata
            tokens_input = usage.prompt_token_count if usage else 0
            tokens_output = usage.candidates_token_count if (usage and usage.candidates_token_count is not None) else 0
            cached_tokens = getattr(usage, "cached_content_token_count", 0) if usage else 0

            print(
                f"[GeminiProvider] API call: {api_time:.2f}s, Total: {total_time:.2f}s, "
                f"Tokens: {tokens_input}/{tokens_output}, Cached: {cached_tokens}"
            )

            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output)

            # Get finish reason safely
            finish_reason = "unknown"
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = response.candidates[0].finish_reason.lower()

            # Record metrics
            metrics = get_metrics()
            metrics.record_success(
                tokens_in=tokens_input,
                tokens_out=tokens_output,
                cost=cost,
                duration_ms=total_time * 1000
            )

            return LLMResponse(
                content=response.text,
                model=self.model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason=finish_reason,
            )

        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            error_msg = f"[GeminiProvider] ⚠️ TIMEOUT after {elapsed:.2f}s (limit: {timeout}s)"
            print(error_msg)
            logger.error(error_msg)
            # Log to Celery worker stdout/stderr
            import sys
            sys.stderr.write(f"{error_msg}\n")
            sys.stderr.flush()
            
            # Record timeout metrics
            metrics = get_metrics()
            metrics.record_failure(is_timeout=True)
            
            raise RuntimeError(f"Gemini API request timed out after {timeout} seconds")
        
        except errors.APIError as e:
            elapsed = time.time() - start_time
            print(
                f"[GeminiProvider] API ERROR after {elapsed:.2f}s: code={e.code}, message={e.message}"
            )
            
            # Record failure metrics
            metrics = get_metrics()
            metrics.record_failure(is_timeout=False)
            
            raise RuntimeError(f"Gemini API error [{e.code}]: {e.message}")
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(
                f"[GeminiProvider] UNEXPECTED ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}"
            )
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Unexpected Gemini error: {str(e)}")

    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_functions: Dict[str, Callable],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
        max_iterations: int = 5,
    ) -> LLMResponse:
        """
        Generate text with Function Calling support.
        
        Implements a multi-turn conversation loop:
        1. Send prompt to Gemini with tool declarations
        2. If Gemini requests function calls, execute them
        3. Send results back to Gemini
        4. Repeat until Gemini returns a final text response
        
        Args:
            prompt: User prompt
            tools: Tool declarations in Gemini format
            tool_functions: Dict mapping function names to callables
            temperature: Sampling temperature
            max_tokens: Max output tokens
            system_prompt: System instruction
            max_iterations: Max function calling iterations to prevent infinite loops
            
        Returns:
            LLMResponse with final text response
        """
        start_time = time.time()
        total_tokens_input = 0
        total_tokens_output = 0
        
        try:
            config_args = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
                "tools": tools,
            }
            
            if system_prompt:
                config_args["system_instruction"] = system_prompt

            config = types.GenerateContentConfig(**config_args)

            # Build conversation history
            # Start with user prompt
            conversation_history = [
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)]
                )
            ]
            
            print(f"[GeminiProvider] Starting function calling loop with {self.model_name}...")
            
            # Multi-turn loop for function calling
            for iteration in range(max_iterations):
                print(f"[GeminiProvider] Iteration {iteration + 1}/{max_iterations}")
                api_start = time.time()
                
                # Generate response
                response = await self.client.aio.models.generate_content(
                    model=self.model_name,
                    contents=conversation_history,
                    config=config,
                )
                
                api_time = time.time() - api_start
                
                # Track token usage
                usage = response.usage_metadata
                if usage:
                    total_tokens_input += usage.prompt_token_count
                    total_tokens_output += usage.candidates_token_count
                    print(f"[GeminiProvider] API call: {api_time:.2f}s, Tokens: {usage.prompt_token_count}/{usage.candidates_token_count}")
                
                # Check if we have a valid response
                if not response.candidates or not response.candidates[0].content.parts:
                    raise RuntimeError("Empty response from Gemini")
                
                candidate = response.candidates[0]
                
                # Extract function calls from response
                function_calls = []
                text_parts = []
                
                for part in candidate.content.parts:
                    if part.function_call:
                        function_calls.append(part.function_call)
                    elif part.text:
                        text_parts.append(part.text)
                
                # If no function calls, we have the final response
                if not function_calls:
                    final_text = "".join(text_parts) if text_parts else response.text
                    total_time = time.time() - start_time
                    cost = self.calculate_cost(total_tokens_input, total_tokens_output)
                    
                    print(f"[GeminiProvider] Completed in {iteration + 1} iterations, {total_time:.2f}s total")
                    
                    return LLMResponse(
                        content=final_text,
                        model=self.model_name,
                        tokens_input=total_tokens_input,
                        tokens_output=total_tokens_output,
                        cost_usd=cost,
                        finish_reason=candidate.finish_reason.name.lower() if candidate.finish_reason else "stop",
                    )
                
                # Execute function calls
                print(f"[GeminiProvider] Executing {len(function_calls)} function call(s)...")
                
                # Add model's response to history (with function calls)
                conversation_history.append(candidate.content)
                
                # Execute each function and collect results
                function_responses = []
                
                for func_call in function_calls:
                    func_name = func_call.name
                    func_args = dict(func_call.args) if func_call.args else {}
                    
                    print(f"[GeminiProvider]   - Calling {func_name}({func_args})")
                    
                    # Get the function
                    if func_name not in tool_functions:
                        error_msg = f"Function '{func_name}' not found in tool_functions"
                        print(f"[GeminiProvider]   ⚠️ {error_msg}")
                        function_responses.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=func_name,
                                    response={"error": error_msg}
                                )
                            )
                        )
                        continue
                    
                    # Execute the function
                    try:
                        func = tool_functions[func_name]
                        
                        # Call function (handle both sync and async)
                        if asyncio.iscoroutinefunction(func):
                            result = await func(**func_args)
                        else:
                            result = func(**func_args)
                        
                        print(f"[GeminiProvider]   ✓ Result: {str(result)[:100]}...")
                        
                        # Add function response
                        function_responses.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=func_name,
                                    response={"result": result}
                                )
                            )
                        )
                        
                    except Exception as e:
                        error_msg = f"Error executing {func_name}: {str(e)}"
                        print(f"[GeminiProvider]   ✗ {error_msg}")
                        logger.exception(f"Function execution error: {func_name}")
                        
                        function_responses.append(
                            types.Part(
                                function_response=types.FunctionResponse(
                                    name=func_name,
                                    response={"error": error_msg}
                                )
                            )
                        )
                
                # Add function responses to conversation history
                conversation_history.append(
                    types.Content(
                        role="user",
                        parts=function_responses
                    )
                )
            
            # If we hit max iterations, return what we have
            print(f"[GeminiProvider] ⚠️ Max iterations ({max_iterations}) reached")
            total_time = time.time() - start_time
            cost = self.calculate_cost(total_tokens_input, total_tokens_output)
            
            return LLMResponse(
                content="I apologize, but I encountered too many function calls. Please try rephrasing your question.",
                model=self.model_name,
                tokens_input=total_tokens_input,
                tokens_output=total_tokens_output,
                cost_usd=cost,
                finish_reason="max_iterations",
            )

        except Exception as e:
            elapsed = time.time() - start_time
            print(
                f"[GeminiProvider] ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}"
            )
            logger.exception("Error in generate_with_tools")
            raise RuntimeError(f"Gemini API error: {str(e)}")

    async def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's tokenizer"""
        response = await self.client.aio.models.count_tokens(
            model=self.model_name,
            contents=text
        )
        return response.total_tokens

    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost in USD"""
        pricing = self.PRICING.get(
            self.model_name, self.PRICING["gemini-2.0-flash-exp"]
        )

        input_cost = tokens_input * pricing["input"]
        output_cost = tokens_output * pricing["output"]

        return input_cost + output_cost

