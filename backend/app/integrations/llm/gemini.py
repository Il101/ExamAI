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
    
    # Request counter for monitoring
    _request_count: int = 0
    _request_count_lock = None  # Will be initialized as asyncio.Lock()

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp", fallback_model: Optional[str] = None):
        """
        Initialize with both a primary model and optional fallback model.
        
        Args:
            api_key: Gemini API key
            model: Primary model name (e.g. 'gemini-2.5-flash')
            fallback_model: Optional fallback model (e.g. 'gemini-2.0-flash')
        """
        self.model_name = model
        self.fallback_model_name = fallback_model
        self.api_key = api_key
        print(f"[GeminiProvider] Initialized with primary_model='{self.model_name}', fallback_model='{self.fallback_model_name}'")
        self.client = self._get_client(api_key)

    @classmethod
    def _get_client(cls, api_key: str) -> genai.Client:
        """
        Get or create a shared genai.Client instance.
        The SDK has built-in retry logic for transient errors (429, 503).
        """
        if cls._shared_client is None or cls._shared_api_key != api_key:
            # Configure retry with jitter to prevent thundering herd
            # Recommended by Vertex AI: max 2 retries, exponential backoff, add jitter
            retry_options = types.HttpRetryOptions(
                attempts=2,               # Only 2 SDK retries to prevent cascade
                initialDelay=1.0,         # Start with 1 second
                maxDelay=10.0,            # Cap at 10 seconds (reduced from 60s)
                expBase=2.0,              # Exponential: 1s -> 2s
                jitter=0.3,               # 30% random variation to desync workers
                httpStatusCodes=[429, 503],  # Retry on rate limit and overload
            )
            
            # Configure HTTP options with timeout and v1beta API (required for caching)
            http_options = types.HttpOptions(
                timeout=240000,  # 240 seconds - must be > highest gen timeout (180s)
                api_version='v1beta',  # Use v1beta for Context Caching support
                retry_options=retry_options,
            )
            
            print(f"[GeminiProvider] Initializing new shared client with timeout=240s, retry=2 attempts with jitter...")
            cls._shared_client = genai.Client(
                api_key=api_key, 
                http_options=http_options,
            )
            cls._shared_api_key = api_key
            
        return cls._shared_client

    @classmethod
    async def _increment_request_count(cls):
        """Increment the global request counter (thread-safe)"""
        if cls._request_count_lock is None:
            import asyncio
            cls._request_count_lock = asyncio.Lock()
        
        async with cls._request_count_lock:
            cls._request_count += 1
            current_count = cls._request_count
        
        # Log every 10 requests
        if current_count % 10 == 0:
            print(f"[GeminiProvider] 📊 Total API requests: {current_count}")
        
        return current_count
    
    @classmethod
    def get_request_stats(cls) -> dict:
        """Get current request statistics"""
        return {
            "total_requests": cls._request_count,
            "timestamp": time.time(),
        }
    
    @classmethod
    def reset_request_count(cls):
        """Reset request counter (for testing/debugging)"""
        cls._request_count = 0
        print("[GeminiProvider] Request counter reset to 0")


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

        # Track API request
        request_num = await self._increment_request_count()
        
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
                f"[GeminiProvider] API ERROR after {elapsed:.2f}s: code={e.code} (type={type(e.code).__name__}), message={e.message}"
            )
            
            # Check if we should try fallback model on 503 (handle both int and str)
            error_code = int(e.code) if isinstance(e.code, str) else e.code
            print(f"[GeminiProvider] DEBUG: error_code={error_code}, fallback_model_name={self.fallback_model_name}, model_name={self.model_name}")
            if error_code == 503 and self.fallback_model_name and self.fallback_model_name != self.model_name:
                print(f"[GeminiProvider] 🔄 Primary model '{self.model_name}' overloaded (503). Trying fallback: '{self.fallback_model_name}'...")
                
                try:
                    # Retry with fallback model using same parameters
                    config_args = {
                        "temperature": temperature,
                        "max_output_tokens": max_tokens,
                    }
                    
                    if system_prompt:
                        if "cache_name" in kwargs and kwargs["cache_name"]:
                            full_prompt = f"{system_prompt}\n\n{prompt}"
                        else:
                            config_args["system_instruction"] = system_prompt
                    else:
                        full_prompt = prompt
                    
                    if "cache_name" in kwargs and kwargs["cache_name"]:
                        config_args["cached_content"] = kwargs["cache_name"]
                    
                    if response_schema:
                        config_args["response_mime_type"] = "application/json"
                        config_args["response_schema"] = response_schema
                    elif response_mime_type:
                        config_args["response_mime_type"] = response_mime_type
                    
                    config = types.GenerateContentConfig(**config_args)
                    
                    # Try fallback model
                    fallback_response = await asyncio.wait_for(
                        self.client.aio.models.generate_content(
                            model=self.fallback_model_name,
                            contents=full_prompt,
                            config=config
                        ),
                        timeout=timeout
                    )
                    
                    # Extract usage stats from fallback
                    usage = fallback_response.usage_metadata
                    tokens_input = usage.prompt_token_count if usage else 0
                    tokens_output = usage.candidates_token_count if (usage and usage.candidates_token_count is not None) else 0
                    
                    total_time = time.time() - start_time
                    print(f"[GeminiProvider] ✅ Fallback succeeded! Model: {self.fallback_model_name}, Time: {total_time:.2f}s")
                    
                    # Calculate cost using fallback model pricing
                    cost = self.calculate_cost(tokens_input, tokens_output, model=self.fallback_model_name)
                    
                    finish_reason = "unknown"
                    if fallback_response.candidates and fallback_response.candidates[0].finish_reason:
                        finish_reason = fallback_response.candidates[0].finish_reason.lower()
                    
                    # Record success metrics for fallback
                    metrics = get_metrics()
                    metrics.record_success(
                        tokens_in=tokens_input,
                        tokens_out=tokens_output,
                        cost=cost,
                        duration_ms=total_time * 1000
                    )
                    
                    return LLMResponse(
                        content=fallback_response.text,
                        model=f"{self.model_name} -> {self.fallback_model_name}",  # Indicate fallback was used
                        tokens_input=tokens_input,
                        tokens_output=tokens_output,
                        cost_usd=cost,
                        finish_reason=finish_reason,
                    )
                    
                except Exception as fallback_error:
                    print(f"[GeminiProvider] ❌ Fallback also failed: {fallback_error}")
                    # Fall through to original error handling
            
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

    async def generate_with_cache(
        self,
        cache_name: str,
        prompt: str,
        temperature: float = 0.3,
        timeout: int = 120,
    ) -> LLMResponse:
        """
        Generate content using cached context.
        
        This method uses the SDK's configured retry logic with jitter,
        unlike direct client.aio.models.generate_content() calls.
        
        Args:
            cache_name: Name of the cached content
            prompt: User prompt (cache content is already loaded)
            temperature: Sampling temperature
            timeout: Request timeout in seconds
            
        Returns:
            LLMResponse with generated content
        """
        from app.core.config import settings
        import asyncio
        
        # Track API request
        request_num = await self._increment_request_count()
        
        start_time = time.time()
        
        try:
            print(f"[GeminiProvider] Generating with cache: {cache_name} (request #{request_num})")
            
            # Use SDK client with configured retry options
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    config={
                        "cached_content": cache_name,
                        "temperature": temperature,
                    },
                    contents=[{"role": "user", "parts": [{"text": prompt}]}]
                ),
                timeout=timeout
            )
            
            elapsed = time.time() - start_time
            
            # Extract response text
            plan_text = response.text
            if plan_text is None:
                raise ValueError("Received None response from cached LLM call")
            
            # Calculate tokens and cost
            tokens_input = response.usage_metadata.prompt_token_count if response.usage_metadata else 0
            tokens_output = response.usage_metadata.candidates_token_count if response.usage_metadata else 0
            cost = self.calculate_cost(tokens_input, tokens_output)
            
            print(
                f"[GeminiProvider] Cache generation completed in {elapsed:.2f}s. "
                f"Tokens: {tokens_input}/{tokens_output}, Cost: ${cost:.6f}"
            )
            
            return LLMResponse(
                content=plan_text,
                model=self.model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason="stop",
            )
            
        except asyncio.TimeoutError:
            elapsed = time.time() - start_time
            error_msg = f"[GeminiProvider] ⚠️ Cache generation TIMEOUT after {elapsed:.2f}s"
            print(error_msg)
            raise RuntimeError(f"Cache generation timed out after {timeout} seconds")
        
        except errors.APIError as e:
            elapsed = time.time() - start_time
            print(f"[GeminiProvider] Cache generation API ERROR after {elapsed:.2f}s: {e.code} - {e.message}")
            raise RuntimeError(f"Gemini API error [{e.code}]: {e.message}")
        
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"[GeminiProvider] Cache generation ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}")
            raise RuntimeError(f"Cache generation error: {str(e)}")

    def calculate_cost(self, tokens_input: int, tokens_output: int, model: Optional[str] = None) -> float:
        """Calculate cost based on token usage for the specified model"""
        model_name = model or self.model_name
        
        # Get pricing for the specified model (with fallback to base model name)
        pricing_key = model_name
        if pricing_key not in self.PRICING:
            # Try without version suffix (e.g., "gemini-2.5-flash-002" -> "gemini-2.5-flash")
            base_model = "-".join(pricing_key.split("-")[:-1]) if pricing_key.split("-")[-1].isdigit() else pricing_key
            pricing_key = base_model if base_model in self.PRICING else "gemini-2.0-flash-exp"
        
        pricing = self.PRICING.get(pricing_key, self.PRICING["gemini-2.0-flash-exp"])
        return (tokens_input * pricing["input"]) + (tokens_output * pricing["output"])
