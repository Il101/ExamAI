import logging
import time
from typing import Any, Optional, List, Dict, Callable

import google.generativeai as genai

from app.integrations.llm.base import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider implementation"""

    # Pricing (as of Nov 2024, verify on https://ai.google.dev/pricing)
    PRICING = {
        "gemini-2.0-flash-exp": {
            "input": 0.00 / 1_000_000,  # Free tier
            "output": 0.00 / 1_000_000,
        },
        "gemini-1.5-flash": {
            "input": 0.075 / 1_000_000,  # $0.075 per 1M tokens
            "output": 0.30 / 1_000_000,  # $0.30 per 1M tokens
        },
        "gemini-1.5-pro": {
            "input": 1.25 / 1_000_000,
            "output": 5.00 / 1_000_000,
        },
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
                full_prompt, generation_config=generation_config
            )
            api_time = time.time() - api_start
            total_time = time.time() - start_time

            # Extract usage stats
            usage = response.usage_metadata
            tokens_input = usage.prompt_token_count
            tokens_output = usage.candidates_token_count

            print(
                f"[GeminiProvider] API call: {api_time:.2f}s, Total: {total_time:.2f}s, Tokens: {tokens_input}/{tokens_output}"
            )

            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output)

            return LLMResponse(
                content=response.text,
                model=self.model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason=response.candidates[0].finish_reason.name.lower(),
            )

        except Exception as e:
            elapsed = time.time() - start_time
            # Log error and re-raise
            print(
                f"[GeminiProvider] ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}"
            )
            import traceback

            traceback.print_exc()
            raise RuntimeError(f"Gemini API error: {str(e)}")

    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_functions: Dict[str, Callable],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> LLMResponse:
        """
        Generate text with Function Calling support.
        
        Args:
            prompt: User prompt
            tools: List of tool declarations in Gemini format
            tool_functions: Dict mapping tool names to actual Python functions
            temperature: Randomness (0.0-1.0)
            max_tokens: Maximum tokens to generate
            system_prompt: System instructions
            
        Returns:
            LLMResponse with content (may include tool call results)
        """
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

            print(f"[GeminiProvider] Calling {self.model_name} API with tools...")
            api_start = time.time()
            
            # Generate with tools
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=generation_config,
                tools=tools,
            )
            
            api_time = time.time() - api_start
            
            # Extract usage stats
            usage = response.usage_metadata
            tokens_input = usage.prompt_token_count
            tokens_output = usage.candidates_token_count

            # Check if model wants to call functions
            function_calls = []
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)

            # Execute function calls if any
            if function_calls:
                print(f"[GeminiProvider] Executing {len(function_calls)} function calls...")
                
                # Execute each function call
                function_responses = []
                for fc in function_calls:
                    func_name = fc.name
                    func_args = dict(fc.args)
                    
                    print(f"[GeminiProvider] Calling {func_name}({func_args})")
                    
                    if func_name in tool_functions:
                        try:
                            # Call the actual function
                            result = await tool_functions[func_name](**func_args)
                            function_responses.append({
                                "name": func_name,
                                "response": {"result": result}
                            })
                        except Exception as e:
                            print(f"[GeminiProvider] Error calling {func_name}: {e}")
                            function_responses.append({
                                "name": func_name,
                                "response": {"error": str(e)}
                            })
                    else:
                        print(f"[GeminiProvider] Unknown function: {func_name}")
                        function_responses.append({
                            "name": func_name,
                            "response": {"error": f"Function {func_name} not found"}
                        })
                
                # Send function results back to model
                print(f"[GeminiProvider] Sending function results back to model...")
                
                # Build parts for the second call
                parts = [response.candidates[0].content.parts[0]]  # Original function call
                for fr in function_responses:
                    parts.append(
                        genai.protos.Part(
                            function_response=genai.protos.FunctionResponse(
                                name=fr["name"],
                                response=fr["response"]
                            )
                        )
                    )
                
                # Second API call with function results
                response2 = await self.model.generate_content_async(
                    parts,
                    generation_config=generation_config,
                )
                
                # Update usage stats
                usage2 = response2.usage_metadata
                tokens_input += usage2.prompt_token_count
                tokens_output += usage2.candidates_token_count
                
                # Use the second response as final
                response = response2

            total_time = time.time() - start_time
            print(
                f"[GeminiProvider] Total time: {total_time:.2f}s, Tokens: {tokens_input}/{tokens_output}"
            )

            # Calculate cost
            cost = self.calculate_cost(tokens_input, tokens_output)

            return LLMResponse(
                content=response.text,
                model=self.model_name,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_usd=cost,
                finish_reason=response.candidates[0].finish_reason.name.lower(),
            )

        except Exception as e:
            elapsed = time.time() - start_time
            print(
                f"[GeminiProvider] ERROR after {elapsed:.2f}s: {type(e).__name__}: {str(e)}"
            )
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
        pricing = self.PRICING.get(
            self.model_name, self.PRICING["gemini-2.0-flash-exp"]
        )

        input_cost = tokens_input * pricing["input"]
        output_cost = tokens_output * pricing["output"]

        return input_cost + output_cost

