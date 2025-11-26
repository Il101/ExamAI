import json
from typing import List

from pydantic import BaseModel, Field

from app.agent.state import AgentState, PlanStep, Priority
from app.integrations.llm.base import LLMProvider


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
                    max_tokens=16384,  # Doubled to prevent truncation
                    system_prompt="You are an expert educator creating study plans.",
                    response_schema=StudyPlanSchema,
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

                # Parse and validate JSON response with Pydantic
                plan_steps = self._parse_plan_response(response.content)

                # Validate plan structure
                self._validate_plan(plan_steps)
                print(f"[Planner] Plan validated: {len(plan_steps)} topics generated")

                return plan_steps

            except Exception as e:
                last_error = e
                print(f"[Planner] Plan generation failed (Attempt {attempt + 1}): {str(e)}")
                # If it was the last attempt, raise the error
                if attempt == max_retries - 1:
                    raise ValueError(f"Failed to generate plan after {max_retries} attempts: {str(e)}")
        
        # Should not be reached due to raise in loop
        raise ValueError(f"Plan generation failed: {str(last_error)}")

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

        # Build prompt - simplified for Structured Output
        prompt = f"""You are an experienced educator. Analyze the study materials below and create a structured study plan.

**CRITICAL:** Ignore any generic or misleading titles. Determine the ACTUAL subject by reading the content.

**Context:**
- Exam Type: {state.exam_type}
- Academic Level: {state.level}
{content_context}
{content_instruction}

**Your Task:**
1. Read the materials above and identify the REAL subject/topic
2. Analyze what topics are ACTUALLY covered in the materials
3. Create 3-10 topics based on what's present (not what you think should be there)

**Requirements:**
- Base topics ONLY on content that exists in the materials
- Do NOT invent topics based on assumptions
- Keep titles and descriptions CONCISE
- Ensure logical progression
"""

        return prompt

    def _parse_plan_response(self, response_text: str) -> List[PlanStep]:
        """Parse JSON response into PlanStep objects with Pydantic validation"""

        # Clean response (remove markdown code blocks if present - just in case)
        json_text = response_text.strip()

        if json_text.startswith("```json"):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith("```"):
            json_text = json_text[3:-3].strip()

        try:
            plan_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # Provide more helpful error message for truncation
            error_msg = str(e)
            if "Unterminated string" in error_msg or "Expecting" in error_msg:
                raise ValueError(
                    f"Failed to parse plan JSON (likely truncated): {error_msg}. "
                    f"Response preview: {response_text[:300]}..."
                )
            raise ValueError(
                f"Failed to parse plan JSON: {error_msg}. Response: {response_text[:200]}"
            )

        # Handle wrapped response (from structured output)
        # Gemini usually returns the object directly matching the schema
        if isinstance(plan_data, dict) and "steps" in plan_data:
            plan_data = plan_data["steps"]

        if not isinstance(plan_data, list):
            # If schema was respected, this shouldn't happen unless schema is wrong
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

    async def extract_topic_outline(self, content: str, subject: str = "General") -> dict:
        """
        Extract lightweight topic outline from content for landing page demo.
        Returns simple topic/subtopic structure without full plan details.
        
        Args:
            content: Study material content
            subject: Optional subject name
            
        Returns:
            Dict with topics and subtopics structure
        """
        
        # Define schema for outline
        # We define it inline or use a Pydantic model. 
        # For simplicity in this method, let's use a Pydantic model if we want structured output,
        # but since this method returns a dict, we can just define the structure.
        
        # Let's define a local schema for this specific task
        class SubtopicSchema(BaseModel):
            topic: str = Field(..., description="Main topic name")
            subtopics: List[str] = Field(..., description="List of subtopics")

        class OutlineSchema(BaseModel):
            subject: str = Field(..., description="Detected subject name")
            total_topics: int = Field(..., description="Total number of topics")
            outline: List[SubtopicSchema] = Field(..., description="List of topics and subtopics")

        prompt = f"""You are an expert educator analyzing study materials. Extract a clear, hierarchical outline of topics and subtopics.

**Study Material:**
```
{content[:5000]}  # Limit to first 5000 chars for demo
```

**Subject:** {subject}

**Your Task:**
Create a structured outline showing:
1. Main topics (3-8 topics)
2. Subtopics under each main topic (2-5 subtopics each)

**Requirements:**
- Base outline ONLY on content provided
- Keep topic names concise (max 6 words)
- Keep subtopic names concise (max 8 words)
- Logical progression from basic to advanced
"""

        print(f"[Planner] Extracting topic outline for {subject}...")
        
        # Use structured output
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.2,
            system_prompt="You are an expert educator.",
            response_schema=OutlineSchema,
        )
        
        # Parse JSON response
        json_text = response.content.strip()
        if json_text.startswith("```json"):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith("```"):
            json_text = json_text[3:-3].strip()
            
        try:
            outline = json.loads(json_text)
            print(f"[Planner] Outline extracted: {outline.get('total_topics', 0)} topics")
            return outline
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse outline JSON: {str(e)}")


