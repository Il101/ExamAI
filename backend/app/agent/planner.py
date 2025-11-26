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
                    max_tokens=4000,
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

**CRITICAL: You MUST return ONLY valid JSON in this EXACT format (no markdown, no code blocks):**

{{
  "total_topics": 8,
  "total_blocks": 3,
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
        }},
        {{
          "id": "topic_02",
          "title": "Basic Terminology",
          "description": "Key terms and definitions",
          "estimated_paragraphs": 3
        }}
      ]
    }}
  ]
}}

**Requirements:**
- Return ONLY the JSON object (no markdown code blocks, no extra text)
- MUST include total_topics and total_blocks fields
- ONLY create topics for content that exists in the materials
- Keep titles and descriptions CONCISE (max 100 chars)
- Ensure logical progression within and across blocks

Generate the JSON plan now:"""

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


