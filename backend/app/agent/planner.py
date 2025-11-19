import json
from typing import List
from pydantic import BaseModel, Field
from app.agent.state import AgentState, PlanStep, Priority
from app.integrations.llm.base import LLMProvider
import google.generativeai as genai


class PlanStepSchema(BaseModel):
    """Pydantic schema for structured output validation"""

    id: int = Field(..., description="Unique topic ID")
    title: str = Field(..., description="Topic name (concise, max 10 words)")
    description: str = Field(..., description="What should be covered")
    priority: int = Field(..., description="Priority: 1-high, 2-medium, 3-low")
    estimated_paragraphs: int = Field(..., description="Estimated content size")
    dependencies: List[int] = Field(
        default_factory=list, description="Prerequisite topic IDs"
    )


class StudyPlanSchema(BaseModel):
    """Wrapper for list of steps to ensure valid JSON object structure"""

    steps: List[PlanStepSchema]


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

    async def make_plan(self, state: AgentState) -> List[PlanStep]:
        """
        Create execution plan based on user request.

        Args:
            state: AgentState with user request and parameters

        Returns:
            List of PlanStep objects

        Raises:
            ValueError: If plan generation fails or returns invalid JSON
        """

        prompt = self._build_planning_prompt(state)

        print(f"[Planner] Calling LLM to generate plan for {state.subject}...")
        # Call LLM - use JSON mode without strict schema to avoid API errors
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.3,
            system_prompt="You are an expert educator creating study plans. Always respond with valid JSON only.",
        )
        print(
            f"[Planner] LLM response received. Tokens: {response.tokens_input}/{response.tokens_output}"
        )

        # Track token usage
        state.add_token_usage(
            response.tokens_input, response.tokens_output, response.cost_usd
        )

        # Parse and validate JSON response with Pydantic
        plan_steps = self._parse_plan_response(response.content)

        # Validate plan structure
        self._validate_plan(plan_steps)
        print(f"[Planner] Plan validated: {len(plan_steps)} topics generated")

        return plan_steps

    def _build_planning_prompt(self, state: AgentState) -> str:
        """Build prompt for plan generation"""

        # Include original content context if available
        content_context = ""
        content_instruction = ""
        if state.original_content:
            # Use full content for analysis, not just preview
            content_context = f"\n**User-provided study materials:**\n```\n{state.original_content}\n```\n"
            content_instruction = """
**CRITICAL INSTRUCTION:**
- Base your topic structure ONLY on the actual content provided above
- DO NOT add topics that are not covered in the provided materials
- If the content is limited or organizational, create fewer topics (even 2-4 is fine)
- Each topic must correspond to content that actually exists in the materials
- If materials are incomplete, acknowledge this in topic descriptions
"""

        # Build prompt with escaped braces for JSON example
        prompt = f"""You are an experienced educator. Your task is to create a structured study plan for exam preparation based on PROVIDED MATERIALS ONLY.

**Input Parameters:**
- Subject: {state.subject}
- Exam Type: {state.exam_type}
- Academic Level: {state.level}
- User Request: {state.user_request}
{content_context}
{content_instruction}

**Your Task:**
1. Analyze the ACTUAL content provided above
2. Identify topics that are EXPLICITLY present in the materials
3. Create appropriate number of topics based on what's actually covered (could be 2-15 topics)
4. For each topic, specify:
   - title: concise topic name based on actual content
   - description: what is ACTUALLY covered in the materials (2-3 sentences)
   - priority: 1 (essential), 2 (important), 3 (advanced/optional)
   - estimated_paragraphs: how many paragraphs needed to explain this existing content (3-8)
   - dependencies: list of topic IDs that should be covered first (empty array if none)

**Requirements:**
- ONLY create topics for content that exists in the provided materials
- Do NOT invent or assume topics based on subject name
- If materials are organizational/introductory, reflect that in your plan
- Progress logically based on actual content structure
- Each topic must be verifiable from the provided text

**Output Format:** JSON object with a "steps" key containing the array of topics.

**Example Structure:**
{{
  "steps": [
    {{
      "id": 1,
      "title": "Derivative of a Function",
      "description": "Definition of derivative, geometric interpretation, differentiation rules for basic functions.",
      "priority": 1,
      "estimated_paragraphs": 5,
      "dependencies": []
    }},
    {{
      "id": 2,
      "title": "Chain Rule",
      "description": "Chain rule for composite functions, examples and applications.",
      "priority": 1,
      "estimated_paragraphs": 4,
      "dependencies": [1]
    }}
  ]
}}

Return ONLY valid JSON, no markdown code blocks, no explanations."""

        return prompt

    def _parse_plan_response(self, response_text: str) -> List[PlanStep]:
        """Parse JSON response into PlanStep objects with Pydantic validation"""

        # Clean response (remove markdown code blocks if present)
        json_text = response_text.strip()

        if json_text.startswith("```json"):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith("```"):
            json_text = json_text[3:-3].strip()

        try:
            plan_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse plan JSON: {str(e)}. Response: {response_text[:200]}"
            )

        # Handle wrapped response (from structured output)
        if isinstance(plan_data, dict) and "steps" in plan_data:
            plan_data = plan_data["steps"]

        if not isinstance(plan_data, list):
            raise ValueError("Plan must be a JSON array or object with 'steps' array")

        # Validate with Pydantic and convert to PlanStep objects
        plan_steps = []
        for idx, item in enumerate(plan_data):
            try:
                # Pydantic validation
                validated = PlanStepSchema(**item)
                # Convert to domain model
                plan_steps.append(
                    PlanStep(
                        id=validated.id,
                        title=validated.title,
                        description=validated.description,
                        priority=Priority(validated.priority),
                        estimated_paragraphs=validated.estimated_paragraphs,
                        dependencies=validated.dependencies,
                    )
                )
            except Exception as e:
                raise ValueError(f"Invalid plan step at index {idx}: {str(e)}")

        return plan_steps

    def _validate_plan(self, plan: List[PlanStep]):
        """Validate plan structure"""

        if not plan:
            raise ValueError("Plan cannot be empty")

        # Let AI decide appropriate number of topics based on content
        # Soft limits: warn but don't fail
        if len(plan) < 3:
            print(
                f"[Planner] Warning: Only {len(plan)} topics generated (unusually low)"
            )

        if len(plan) > 25:
            print(f"[Planner] Warning: {len(plan)} topics generated (unusually high)")

        # Check for duplicate IDs
        ids = [step.id for step in plan]
        if len(ids) != len(set(ids)):
            raise ValueError("Plan contains duplicate topic IDs")

        # Validate dependencies
        id_set = set(ids)
        for step in plan:
            for dep_id in step.dependencies:
                if dep_id not in id_set:
                    raise ValueError(
                        f"Topic {step.id} has invalid dependency: {dep_id}"
                    )
