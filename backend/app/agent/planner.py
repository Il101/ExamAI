import json
from typing import List
from pydantic import BaseModel, Field
from app.agent.state import AgentState, PlanStep, Priority
from app.integrations.llm.base import LLMProvider
import google.generativeai as genai


class PlanStepSchema(BaseModel):
    """Pydantic schema for structured output validation"""
    id: int = Field(..., description="Unique topic ID")
    title: str = Field(..., min_length=2, description="Topic name")
    description: str = Field(..., min_length=10, description="What should be covered")
    priority: int = Field(..., ge=1, le=3, description="Priority: 1-high, 2-medium, 3-low")
    estimated_paragraphs: int = Field(..., ge=3, le=20, description="Estimated content size")
    dependencies: List[int] = Field(default_factory=list, description="Prerequisite topic IDs")


class CoursePlanner:
    """
    Planner component: Creates structured plan for exam content.
    Makes ONE LLM call to generate topic structure.
    Uses Gemini native structured output for guaranteed valid JSON.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        # Configure Gemini for structured output
        # We assume Gemini provider supports it if it's the GeminiProvider class
        # But we can also check if the provider has 'model' attribute which implies it's wrapping a model object
        if hasattr(llm_provider, 'model'):
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
        
        # Call LLM with structured output configuration
        if self.use_structured_output:
            # Use Gemini native structured output - guarantees valid JSON
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                system_prompt="You are an expert educator creating study plans.",
                response_schema=list[PlanStepSchema]  # Schema enforcement
            )
        else:
            # Fallback to regular generation
            response = await self.llm.generate(
                prompt=prompt,
                temperature=0.3,
                system_prompt="You are an expert educator creating study plans."
            )
        
        # Track token usage
        state.add_token_usage(
            response.tokens_input,
            response.tokens_output,
            response.cost_usd
        )
        
        # Parse and validate JSON response with Pydantic
        plan_steps = self._parse_plan_response(response.content)
        
        # Validate plan structure
        self._validate_plan(plan_steps)
        
        return plan_steps
    
    def _build_planning_prompt(self, state: AgentState) -> str:
        """Build prompt for plan generation"""
        
        # Include original content context if available
        content_context = ""
        if state.original_content:
            content_preview = state.original_content[:1000]  # First 1000 chars
            content_context = f"\n**User-provided materials (preview):**\n{content_preview}...\n"
        
        return f'''You are an experienced educator. Your task is to create a structured study plan for exam preparation.

**Input Parameters:**
- Subject: {state.subject}
- Exam Type: {state.exam_type}
- Academic Level: {state.level}
- User Request: {state.user_request}
{content_context}

**Your Task:**
1. Break down the subject into 8-15 key topics
2. For each topic, specify:
   - title: concise topic name
   - description: what should be covered (2-3 sentences)
   - priority: 1 (essential), 2 (important), 3 (advanced/optional)
   - estimated_paragraphs: how many paragraphs needed (3-8)
   - dependencies: list of topic IDs that should be covered first (empty array if none)

**Requirements:**
- Start with foundational topics (priority 1)
- Progress logically from basics to advanced concepts
- Each topic should be self-contained but can reference prerequisites
- Avoid overlapping content between topics

**Output Format:** JSON array of objects only, no additional text.

**Example Structure:**
[
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

Return ONLY valid JSON, no markdown code blocks, no explanations.'''
    
    def _parse_plan_response(self, response_text: str) -> List[PlanStep]:
        """Parse JSON response into PlanStep objects with Pydantic validation"""
        
        # Clean response (remove markdown code blocks if present)
        json_text = response_text.strip()
        
        if json_text.startswith('```json'):
            json_text = json_text[7:-3].strip()
        elif json_text.startswith('```'):
            json_text = json_text[3:-3].strip()
        
        try:
            plan_data = json.loads(json_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse plan JSON: {str(e)}. Response: {response_text[:200]}")
        
        if not isinstance(plan_data, list):
            raise ValueError("Plan must be a JSON array")
        
        # Validate with Pydantic and convert to PlanStep objects
        plan_steps = []
        for idx, item in enumerate(plan_data):
            try:
                # Pydantic validation
                validated = PlanStepSchema(**item)
                # Convert to domain model
                plan_steps.append(PlanStep(
                    id=validated.id,
                    title=validated.title,
                    description=validated.description,
                    priority=Priority(validated.priority),
                    estimated_paragraphs=validated.estimated_paragraphs,
                    dependencies=validated.dependencies
                ))
            except Exception as e:
                raise ValueError(f"Invalid plan step at index {idx}: {str(e)}")
        
        return plan_steps
    
    def _validate_plan(self, plan: List[PlanStep]):
        """Validate plan structure"""
        
        if not plan:
            raise ValueError("Plan cannot be empty")
        
        if len(plan) < 5:
            raise ValueError("Plan must have at least 5 topics")
        
        if len(plan) > 20:
            raise ValueError("Plan cannot exceed 20 topics")
        
        # Check for duplicate IDs
        ids = [step.id for step in plan]
        if len(ids) != len(set(ids)):
            raise ValueError("Plan contains duplicate topic IDs")
        
        # Validate dependencies
        id_set = set(ids)
        for step in plan:
            for dep_id in step.dependencies:
                if dep_id not in id_set:
                    raise ValueError(f"Topic {step.id} has invalid dependency: {dep_id}")
