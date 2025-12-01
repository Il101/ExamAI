import json
from typing import List

from pydantic import BaseModel, Field

from app.agent.state import AgentState
from app.integrations.llm.base import LLMProvider
from app.agent.schemas import ExamPlan

# Legacy schemas removed - using ExamPlan from schemas.py


class CoursePlanner:
    """
    Planner component: Creates structured plan for exam content.
    Makes ONE LLM call to generate topic structure.
    Uses Gemini native structured output for guaranteed valid JSON.
    """

    def __init__(self, llm_provider: LLMProvider, max_topics: int | None = None):
        self.llm = llm_provider
        self.max_topics = max_topics  # None = no limit, let AI decide
        # Configure Gemini for structured output
        # We assume Gemini provider supports it if it's the GeminiProvider class
        # But we can also check if the provider has 'model' attribute which implies it's wrapping a model object
        if hasattr(llm_provider, "model"):
            # Use native structured output mode
            self.use_structured_output = True
        else:
            self.use_structured_output = False

    async def make_plan(self, state: AgentState) -> "ExamPlan":
        """
        Generate structured exam plan from user request and materials.
        Returns block-based plan with topics grouped into logical chapters.

        Args:
            state: AgentState with user request and optional original content

        Returns:
            ExamPlan with blocks and topics

        Raises:
            ValueError: If plan generation fails after retries
        """
        from app.agent.schemas import ExamPlan

        prompt = self._build_planning_prompt(state)

        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                print(f"[Planner] Calling LLM to generate plan for {state.subject} (Attempt {attempt + 1}/{max_retries})...")
                
                # Call LLM with structured output schema
                # Increased max_tokens to prevent truncation
                response = await self.llm.generate(
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=16000,
                    response_mime_type="application/json",
                    system_prompt="You are an expert educator creating study plans.",
                    response_schema=ExamPlan,  # Use new ExamPlan schema
                )
                print(
                    f"[Planner] LLM response received. Tokens: {response.tokens_input}/{response.tokens_output}, Finish: {response.finish_reason}"
                )
                
                # Check if response was truncated
                if response.finish_reason == 'length':
                    print(f"[Planner] WARNING: Response truncated (finish_reason=length). Retrying with shorter prompt...")
                    raise ValueError("Response truncated due to max_tokens limit. Retry needed.")

                # Track token usage
                state.add_token_usage(
                    response.tokens_input, response.tokens_output, response.cost_usd
                )

                # Parse and validate
                plan = self._parse_plan_response(response.content)
                self._validate_plan(plan)
                
                print(f"[Planner] Plan validated: {plan.total_blocks} blocks, {plan.total_topics} topics")
                
                # Convert to legacy format for backward compatibility
                from app.agent.plan_adapter import exam_plan_to_steps
                legacy_steps = exam_plan_to_steps(plan)
                
                return legacy_steps

            except Exception as e:
                last_error = e
                print(f"[Planner] Plan generation failed (Attempt {attempt + 1}): {str(e)}")
                # If it was the last attempt, raise the error
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate plan after {max_retries} attempts: {str(e)}")
        
        # Should not be reached due to raise in loop
        raise ValueError(f"Plan generation failed: {str(last_error)}")

    def _build_planning_prompt(self, state: AgentState) -> str:
        """Build prompt for block-based plan generation"""
        from app.prompts import load_prompt

        # Include original content context if available
        content_context = ""
        if state.original_content:
            content_context = f"\n**Study materials to analyze:**\n```\n{state.original_content}\n```\n"

        # Load prompt template and substitute variables
        prompt = load_prompt(
            'planner/course_plan.txt',
            content_context=content_context
        )

        return prompt


    def _parse_plan_response(self, response_text: str) -> "ExamPlan":
        """Parse JSON response into ExamPlan object with Pydantic validation"""
        from app.agent.schemas import ExamPlan
        
        # Clean response (remove markdown code blocks if present)
        json_text = response_text.strip()

        if json_text.startswith("```json"):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith("```"):
            json_text = json_text[3:-3].strip()

        try:
            # Parse and validate with Pydantic
            plan = ExamPlan.model_validate_json(json_text)
            return plan
        except Exception as e:
            error_msg = str(e)
            if "Unterminated string" in error_msg or "Expecting" in error_msg:
                raise ValueError(
                    f"Failed to parse plan JSON (likely truncated): {error_msg}. "
                    f"Response preview: {response_text[:300]}..."
                )
            raise ValueError(
                f"Failed to parse plan JSON: {error_msg}. Response: {response_text[:200]}"
            )


    def _validate_plan(self, plan: ExamPlan):
        """Validate plan structure"""
        
        if not plan.blocks:
            raise ValueError("Plan must have at least one block")
        
        if plan.total_blocks != len(plan.blocks):
            raise ValueError(f"total_blocks mismatch: declared {plan.total_blocks}, got {len(plan.blocks)}")
        
        all_topics = plan.get_all_topics()
        if plan.total_topics != len(all_topics):
            raise ValueError(f"total_topics mismatch: declared {plan.total_topics}, got {len(all_topics)}")
        
        if len(all_topics) < 2:
            raise ValueError(f"Plan must have at least 2 topics, got {len(all_topics)}")
        
        # Validate topic IDs are unique
        topic_ids = [t.id for t in all_topics]
        if len(topic_ids) != len(set(topic_ids)):
            raise ValueError("Topic IDs must be unique")
        
        # Validate block IDs are unique
        block_ids = [b.block_id for b in plan.blocks]
        if len(block_ids) != len(set(block_ids)):
            raise ValueError("Block IDs must be unique")
        
        print(f"[Planner] Plan validated: {plan.total_blocks} blocks, {plan.total_topics} topics")



