import asyncio
import logging
import time
from typing import Any, Optional, List, Dict, Callable

from google import genai
from google.genai import types, errors

from app.core.config import settings
from app.integrations.llm.base import LLMProvider, LLMResponse
from app.integrations.llm.metrics import get_metrics, record_usage_to_db

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation using google-genai SDK"""

    # Pricing (as of late 2025, verify on https://ai.google.dev/pricing)
    # Tiered pricing applies to Gemini 1.5 Series (prices double > 128K).
    # Newer models (2.0+) have different caching/tiering strategies.
    PRICING = {
        # Gemini 3.0 Series (Preview)
        "gemini-3-flash": {
            "input": 0.50 / 1_000_000,
            "output": 3.00 / 1_000_000,
            "cache": 0.05 / 1_000_000,  # 90% discount on processing
        },
        
        # Gemini 2.5 Series
        "gemini-2.5-flash": {
            "input": 0.30 / 1_000_000,
            "output": 2.50 / 1_000_000,
            "cache": 0.03 / 1_000_000,  # 90% discount on processing
        },
        "gemini-2.5-flash-lite": {
            "input": 0.10 / 1_000_000,
            "output": 0.40 / 1_000_000,
            "cache": 0.01 / 1_000_000,  # 90% discount on processing
        },
        
        # Gemini 2.0 Series
        "gemini-2.0-flash": {
            "input": 0.10 / 1_000_000,
            "output": 0.40 / 1_000_000,
            "cache": 0.025 / 1_000_000, # 75% discount on processing
        },
        "gemini-2.0-flash-exp": {
            "input": 0.0,
            "output": 0.0,
            "cache": 0.0,
        },
        
        # Gemini 1.5 Series (Tiered: <128K and >128K)
        # We store as lists: [tier1_rate, tier2_rate]
        "gemini-1.5-pro": {
            "input": [1.25 / 1_000_000, 2.50 / 1_000_000],
            "output": [5.00 / 1_000_000, 10.00 / 1_000_000],
            "cache": [0.3125 / 1_000_000, 0.625 / 1_000_000], # 75% discount
        },
        "gemini-1.5-flash": {
            "input": [0.075 / 1_000_000, 0.15 / 1_000_000],
            "output": [0.30 / 1_000_000, 0.60 / 1_000_000],
            "cache": [0.01875 / 1_000_000, 0.0375 / 1_000_000], # 75% discount
        },
        "gemini-1.5-flash-8b": {
            "input": [0.0375 / 1_000_000, 0.075 / 1_000_000],
            "output": [0.15 / 1_000_000, 0.30 / 1_000_000],
            "cache": [0.01 / 1_000_000, 0.02 / 1_000_000],
        }
    }

    # Shared request counter (still useful for monitoring)
    _request_count: int = 0
    _request_count_lock = None  # Will be initialized as asyncio.Lock()

    def __init__(self, api_key: str, model: Optional[str] = None, fallback_model: Optional[str] = None):
        """
        Initialize with both a primary model and optional fallback model.
        
        Args:
            api_key: Gemini API key
            model: Primary model name (e.g. from settings)
            fallback_model: Optional fallback model (e.g. from settings)
        """
        self.model_name = model or settings.GEMINI_MODEL
        self.fallback_model_name = fallback_model or settings.GEMINI_FALLBACK_MODEL
        self.api_key = api_key
        print(f"[GeminiProvider] Initialized with primary_model='{self.model_name}', fallback_model='{self.fallback_model_name}'")
        self.client = self._get_client(api_key)

    def _get_client(self, api_key: str) -> genai.Client:
        """
        Create a new genai.Client instance.
        
        IMPORTANT: We do NOT share clients across instances anymore.
        Sharing clients across Celery tasks or different event loops causes 
        'RuntimeError: Event loop is closed' because the client's internal 
        HTTPX session is bound to a specific loop that gets closed.
        """
        # Configure retry with jitter to prevent thundering herd
        retry_options = types.HttpRetryOptions(
            attempts=5,
            initialDelay=1.0,
            maxDelay=30.0,
            expBase=2.0,
            jitter=0.3,
            httpStatusCodes=[429, 503],
        )
        
        # Configure HTTP options
        http_options = types.HttpOptions(
            timeout=240000,
            api_version='v1beta',
            retry_options=retry_options,
        )
        
        print(f"[GeminiProvider] Initializing new client with timeout=240s")
        return genai.Client(
            api_key=api_key, 
            http_options=http_options,
        )

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
            # Allow passing non-string contents payloads (e.g., [uploaded_file, prompt]).
            contents_payload = kwargs.get("contents")

            # Combine system prompt with user prompt
            full_prompt = prompt
            
            # Prepare config
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
                
                # Gemini API does NOT support additionalProperties: True in the schema,
                # which Pydantic/google-genai SDK often adds by default.
                # We must strip them recursively if they exist.
                processed_schema = response_schema
                if hasattr(response_schema, "model_json_schema"):
                    # It's a Pydantic V2 model
                    processed_schema = response_schema.model_json_schema()
                elif hasattr(response_schema, "schema"):
                    # It's a Pydantic V1 model
                    processed_schema = response_schema.schema()
                
                if isinstance(processed_schema, dict):
                    processed_schema = self._strip_additional_properties(processed_schema)
                
                config_args["response_schema"] = processed_schema
            elif response_mime_type:
                config_args["response_mime_type"] = response_mime_type

            config = types.GenerateContentConfig(**config_args)

            # Allow model override
            model_to_use = kwargs.get("model", self.model_name)

            print(f"[GeminiProvider] Calling {model_to_use} API with timeout={timeout}s...")
            api_start = time.time()
            
            # Wrap in asyncio.wait_for for guaranteed timeout
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=model_to_use,
                    contents=contents_payload if contents_payload is not None else full_prompt,
                    config=config
                ),
                timeout=timeout
            )
            
            api_time = time.time() - api_start
            total_time = time.time() - start_time

            # Extract usage stats
            usage = response.usage_metadata
            tokens_input = (usage.prompt_token_count or 0) if usage else 0
            tokens_output = (usage.candidates_token_count or 0) if usage else 0
            cached_tokens = (getattr(usage, "cached_content_token_count", 0) or 0) if usage else 0

            print(
                f"[GeminiProvider] API call: {api_time:.2f}s, Total: {total_time:.2f}s, "
                f"Tokens: {tokens_input}/{tokens_output}, Cached: {cached_tokens}"
            )

            # Calculate cost (including cached tokens)
            cost = self.calculate_cost(tokens_input, tokens_output, tokens_cached=cached_tokens, model=model_to_use)

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

            # Persistent DB logging (background)
            asyncio.create_task(
                record_usage_to_db(
                    model_name=model_to_use,
                    provider="gemini",
                    operation_type=kwargs.get("operation_type", "generate"),
                    input_tokens=tokens_input,
                    output_tokens=tokens_output,
                    cost_usd=cost,
                    duration_ms=total_time * 1000,
                    cache_hit=cached_tokens > 0,
                    request_metadata={
                        "request_num": request_num,
                        "finish_reason": finish_reason,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
            )

            # Auto-parse if response_schema is a Pydantic model
            parsed_obj = None
            if response_schema and hasattr(response_schema, "model_validate_json"):
                try:
                    # Clean up response.text (strip markdown code blocks if any)
                    clean_text = response.text.strip()
                    if clean_text.startswith("```json"):
                        clean_text = clean_text[7:].strip()
                        if clean_text.endswith("```"):
                            clean_text = clean_text[:-3].strip()
                    elif clean_text.startswith("```"):
                        clean_text = clean_text[3:].strip()
                        if clean_text.endswith("```"):
                            clean_text = clean_text[:-3].strip()
                    
                    parsed_obj = response_schema.model_validate_json(clean_text)
                except Exception as parse_error:
                    logger.warning(f"[GeminiProvider] Failed to parse response into {response_schema.__name__}: {parse_error}")

            return LLMResponse(
                content=response.text,
                model=model_to_use,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason=finish_reason,
                parsed=parsed_obj,
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

            # Persistent DB logging for timeout (background)
            elapsed = time.time() - start_time
            asyncio.create_task(
                record_usage_to_db(
                    model_name=self.model_name,
                    provider="gemini",
                    operation_type=kwargs.get("operation_type", "generate"),
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0,
                    duration_ms=elapsed * 1000,
                    error_occurred=True,
                    error_message=f"Timeout after {timeout}s",
                    request_metadata={"request_num": request_num}
                )
            )
            
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
                            contents=contents_payload if contents_payload is not None else full_prompt,
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

            # Persistent DB logging for error (background)
            elapsed = time.time() - start_time
            asyncio.create_task(
                record_usage_to_db(
                    model_name=self.model_name,
                    provider="gemini",
                    operation_type=kwargs.get("operation_type", "generate"),
                    input_tokens=0,
                    output_tokens=0,
                    cost_usd=0,
                    duration_ms=elapsed * 1000,
                    error_occurred=True,
                    error_message=f"Gemini API error [{e.code}]: {e.message}",
                    request_metadata={"request_num": request_num}
                )
            )
            
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
                    turn_input = usage.prompt_token_count or 0
                    turn_output = usage.candidates_token_count or 0
                    turn_cached = getattr(usage, "cached_content_token_count", 0) or 0
                    
                    total_tokens_input += turn_input
                    total_tokens_output += turn_output
                    print(f"[GeminiProvider] API call: {api_time:.2f}s, Tokens: {turn_input}/{turn_output}, Cached: {turn_cached}")
                    
                    # Record individual turn usage to DB (background)
                    asyncio.create_task(
                        record_usage_to_db(
                            model_name=self.model_name,
                            provider="gemini",
                            operation_type="tool_call_turn",
                            input_tokens=turn_input,
                            output_tokens=turn_output,
                            cost_usd=self.calculate_cost(turn_input, turn_output, tokens_cached=turn_cached),
                            duration_ms=api_time * 1000,
                            cache_hit=turn_cached > 0,
                            request_metadata={"iteration": iteration + 1}
                        )
                    )
                
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
        # Track API request
        request_num = await self._increment_request_count()
        
        start_time = time.time()
        
        try:
            print(f"[GeminiProvider] Generating with cache: {cache_name} (request #{request_num})")
            
            # Use SDK client with configured retry options
            response = await asyncio.wait_for(
                self.client.aio.models.generate_content(
                    model=self.model_name,
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
            tokens_input = (response.usage_metadata.prompt_token_count or 0) if response.usage_metadata else 0
            tokens_output = (response.usage_metadata.candidates_token_count or 0) if response.usage_metadata else 0
            tokens_cached = (getattr(response.usage_metadata, "cached_content_token_count", 0) or 0) if response.usage_metadata else 0
            
            cost = self.calculate_cost(tokens_input, tokens_output, tokens_cached=tokens_cached)
            
            # Persistent DB logging (background)
            asyncio.create_task(
                record_usage_to_db(
                    model_name=self.model_name,
                    provider="gemini",
                    operation_type="generate_with_cache",
                    input_tokens=tokens_input,
                    output_tokens=tokens_output,
                    cost_usd=cost,
                    duration_ms=elapsed * 1000,
                    cache_hit=True,
                    request_metadata={
                        "request_num": request_num,
                        "cache_name": cache_name
                    }
                )
            )
            
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

    def _strip_additional_properties(self, schema: Any) -> Any:
        """
        Recursively strip 'additionalProperties' from a JSON schema dictionary.
        Gemini API fails if this key is present.
        """
        if not isinstance(schema, dict):
            return schema
            
        # Create a copy to avoids side effects
        cleaned = {k: self._strip_additional_properties(v) for k, v in schema.items() if k != "additionalProperties"}
        
        # Also clean up any $defs or definitions
        for key in ["$defs", "definitions"]:
            if key in cleaned and isinstance(cleaned[key], dict):
                cleaned[key] = {
                    def_name: self._strip_additional_properties(def_val)
                    for def_name, def_val in cleaned[key].items()
                }
                
        return cleaned

    def calculate_cost(self, tokens_input: Optional[int], tokens_output: Optional[int], tokens_cached: Optional[int] = 0, model: Optional[str] = None) -> float:
        """
        Calculate cost based on token usage for the specified model.
        Handles tiered pricing (threshold: 128k tokens) and context caching processing.
        """
        # Null-safety: default to 0 if any token count is None
        tokens_input = tokens_input or 0
        tokens_output = tokens_output or 0
        tokens_cached = tokens_cached or 0
        
        model_name = model or self.model_name
        
        # Get pricing key (strip potential version suffix)
        pricing_key = model_name
        if pricing_key not in self.PRICING:
            parts = pricing_key.split("-")
            if len(parts) > 1 and parts[-1].isdigit():
                base_model = "-".join(parts[:-1])
                if base_model in self.PRICING:
                    pricing_key = base_model
        
        pricing = self.PRICING.get(pricing_key, self.PRICING.get(settings.GEMINI_MODEL, self.PRICING["gemini-1.5-flash"]))
        
        # Determine tier index (based on total prompt size: input + cached)
        # Threshold: 128,000 tokens
        total_prompt = tokens_input + tokens_cached
        tier_idx = 1 if total_prompt > 128000 else 0
        
        # Extract rates
        input_rate = pricing["input"][tier_idx] if isinstance(pricing["input"], list) else pricing["input"]
        output_rate = pricing["output"][tier_idx] if isinstance(pricing["output"], list) else pricing["output"]
        cache_rate = pricing["cache"][tier_idx] if isinstance(pricing.get("cache"), list) else pricing.get("cache", input_rate * 0.25)
        
        # Total cost = (Input * Rate) + (Output * Rate) + (Cached * CacheRate)
        # Note: tokens_input here is the non-cached part of the prompt.
        total_cost = (tokens_input * input_rate) + (tokens_output * output_rate) + (tokens_cached * cache_rate)
        
        # Debug pricing (very useful for the user's specific request)
        if total_cost > 0:
            print(f"[GeminiProvider] Pricing: model='{model_name}', tier={tier_idx+1}, cost=${total_cost:.6f}")
            
        return total_cost
