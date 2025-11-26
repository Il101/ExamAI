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
        """Build prompt for block-based plan generation"""

        # Include original content context if available
        content_context = ""
        if state.original_content:
            content_context = f"\n**Study materials to analyze:**\n```\n{state.original_content}\n```\n"

        # Build prompt for block-based structure
        prompt = f"""You are an educational content analyst. Analyze the study materials and create a structured learning plan.

**CRITICAL:** Determine the subject from the CONTENT ITSELF, not from any title or filename.

{content_context}

**Your task:**
1. Read the materials above and identify the REAL subject/topic
2. Divide content into logical BLOCKS (chapters/modules)
3. Within each block, define 2-5 TOPICS (specific concepts)
4. Each block should be completable in one study session (20-30 min)

**Block Strategy:**
- Block = coherent chapter/module (e.g., "Introduction to Python", "Control Flow")
- Topic = specific concept within block (e.g., "Variables", "Data Types")
- Aim for 3-6 blocks total
- Keep blocks balanced in size
- Base ONLY on content that exists in the materials

**Output as JSON matching this exact schema:**
{{
  "total_topics": <number>,
  "total_blocks": <number>,
  "blocks": [
    {{
      "block_id": "block_01",
      "block_title": "Introduction",
      "topics": [
        {{
          "id": "topic_01",
          "title": "Core Concepts",
          "description": "Fundamental principles",
          "estimated_paragraphs": 4
        }}
      ]
    }}
  ]
}}

**Requirements:**
- ONLY create topics for content that exists in the materials
- Do NOT invent topics based on assumptions
- Keep titles and descriptions CONCISE (max 100 chars)
- Ensure logical progression within and across blocks

Generate plan now:"""

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


