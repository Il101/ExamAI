# Stage 5: AI Agent - Plan-and-Execute Pattern

**Time:** 4-5 days  
**Goal:** Implement Plan-and-Execute AI agent for structured exam content generation

## 5.1 Agent Architecture Overview

### Philosophy
- **Plan-and-Execute Pattern**: Split large task into planning → execution → finalization
- **Sequential Processing**: One topic at a time, not everything in one prompt
- **State Management**: Central state object tracks progress
- **Prompt Engineering**: Specific, focused prompts for each stage

### Architecture Diagram
```
┌──────────────────────────────────────────────────────────┐
│                    Orchestrator                          │
│  Manages: Plan → Execute → Finalize lifecycle            │
└────────────┬─────────────────────────────────┬───────────┘
             │                                 │
     ┌───────▼────────┐              ┌────────▼──────────┐
     │   Planner      │              │    Executor       │
     │  Creates plan  │──────────────▶│  Generates topics│
     │  (1 LLM call)  │              │  (N LLM calls)   │
     └────────────────┘              └───────────────────┘
                                              │
                                     ┌────────▼──────────┐
                                     │    Finalizer      │
                                     │  Assembles notes  │
                                     │  (1 LLM call)     │
                                     └───────────────────┘
```

---

## 5.2 Agent State & Data Structures

### Step 5.2.1: Plan Step Structure
```python
# backend/app/agent/state.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Priority(int, Enum):
    """Priority levels for plan steps"""
    HIGH = 1      # Must-have topics
    MEDIUM = 2    # Important topics
    LOW = 3       # Optional/advanced topics


@dataclass
class PlanStep:
    """
    One step in the execution plan (one topic to generate).
    """
    id: int
    title: str  # Topic name
    description: str  # What should be covered
    priority: Priority = Priority.MEDIUM
    estimated_paragraphs: int = 5  # Estimated content size
    dependencies: List[int] = field(default_factory=list)  # IDs of prerequisite topics
    
    def __post_init__(self):
        if not self.title or len(self.title.strip()) < 2:
            raise ValueError("Title must be at least 2 characters")
        
        if not self.description or len(self.description.strip()) < 10:
            raise ValueError("Description must be at least 10 characters")
        
        if not 1 <= self.estimated_paragraphs <= 20:
            raise ValueError("Estimated paragraphs must be between 1 and 20")


class ExecutionStatus(str, Enum):
    """Agent execution status"""
    NOT_STARTED = "not_started"
    PLANNING = "planning"
    EXECUTING = "executing"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"  # Some topics succeeded
    FAILED = "failed"


@dataclass
class StepResult:
    """Result of executing one step with metadata"""
    step_id: int
    content: str
    success: bool
    error_message: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    timestamp: str = ""
    
    
@dataclass
class AgentState:
    """
    Central state object for the agent.
    Tracks progress through plan execution with granular error handling.
    """
    
    # Input parameters
    user_request: str  # Original user request
    subject: str  # Subject name
    exam_type: str  # oral, written, test
    level: str  # school, bachelor, master, phd
    original_content: str = ""  # User-provided study materials (optional)
    
    # Execution state
    plan: List[PlanStep] = field(default_factory=list)
    current_step_index: int = 0
    results: Dict[int, StepResult] = field(default_factory=dict)  # step_id -> result with metadata
    failed_steps: List[int] = field(default_factory=list)  # IDs of failed steps
    status: ExecutionStatus = ExecutionStatus.NOT_STARTED
    
    # Final output
    final_notes: str = ""
    
    # Metadata
    total_tokens_used: int = 0
    total_cost_usd: float = 0.0
    error_log: List[str] = field(default_factory=list)  # Track all errors
    
    def is_complete(self) -> bool:
        """Check if all steps are executed (including partial completion)"""
        return self.current_step_index >= len(self.plan)
    
    def has_successful_results(self) -> bool:
        """Check if at least some steps succeeded"""
        return len([r for r in self.results.values() if r.success]) > 0
    
    def get_success_rate(self) -> float:
        """Get success rate of executed steps (0.0 to 1.0)"""
        if not self.results:
            return 0.0
        successful = len([r for r in self.results.values() if r.success])
        return successful / len(self.results)
    
    def get_current_step(self) -> Optional[PlanStep]:
        """Get current step to execute"""
        if self.is_complete():
            return None
        return self.plan[self.current_step_index]
    
    def get_progress_percentage(self) -> float:
        """Get completion progress (0.0 to 1.0)"""
        if not self.plan:
            return 0.0
        return self.current_step_index / len(self.plan)
    
    def can_continue_after_failure(self) -> bool:
        """Check if execution can continue despite failures"""
        # Can continue if at least 50% of steps succeeded
        return self.get_success_rate() >= 0.5
    
    def log_error(self, error: str):
        """Log an error message"""
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat()
        self.error_log.append(f"[{timestamp}] {error}")
    
    def add_token_usage(self, tokens_input: int, tokens_output: int, cost: float):
        """Track token usage and costs"""
        self.total_tokens_used += tokens_input + tokens_output
        self.total_cost_usd += cost
```

---

## 5.3 Planner - Structure Generation

### Step 5.3.1: Planner Implementation
```python
# backend/app/agent/planner.py
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
```

---

## 5.4 Executor - Topic Generation

### Step 5.4.1: Executor Implementation
```python
# backend/app/agent/executor.py
from app.agent.state import AgentState, PlanStep
from app.integrations.llm.base import LLMProvider


class TopicExecutor:
    """
    Executor component: Generates content for individual topics.
    Makes N LLM calls (one per topic in plan).
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
    
    async def execute_step(self, state: AgentState) -> str:
        """
        Generate content for current step.
        
        Args:
            state: AgentState with plan and current step index
        
        Returns:
            Generated content for the topic
        """
        
        current_step = state.get_current_step()
        if not current_step:
            raise ValueError("No current step to execute")
        
        # Build context from previous results
        previous_context = self._build_previous_context(state, current_step)
        
        # Build execution prompt
        prompt = self._build_execution_prompt(state, current_step, previous_context)
        
        # Call LLM
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.7,  # Higher temperature for creative content
            max_tokens=2000,  # Limit per topic
            system_prompt="You are an expert educator writing study notes."
        )
        
        # Track usage
        state.add_token_usage(
            response.tokens_input,
            response.tokens_output,
            response.cost_usd
        )
        
        return response.content.strip()
    
    def _build_previous_context(self, state: AgentState, current_step: PlanStep) -> str:
        """
        Build rich context from prerequisite topics.
        Now includes summaries, not just titles, for better coherence.
        """
        
        if not current_step.dependencies:
            # If no explicit dependencies, show all previous topics
            if state.current_step_index == 0:
                return ""
            
            context_parts = ["**Previously covered topics:**"]
            
            for i in range(state.current_step_index):
                step = state.plan[i]
                result = state.results.get(step.id)
                
                if result and result.success:
                    # Extract summary from content (first 2-3 sentences)
                    summary = self._extract_summary(result.content)
                    context_parts.append(f"- **{step.title}**: {summary}")
                else:
                    # Just mention the title if failed
                    context_parts.append(f"- **{step.title}** (coverage incomplete)")
            
            return "\n".join(context_parts)
        
        # Get detailed context for prerequisite topics
        prereq_context = []
        for dep_id in current_step.dependencies:
            dep_step = next((s for s in state.plan if s.id == dep_id), None)
            result = state.results.get(dep_id)
            
            if dep_step and result and result.success:
                summary = self._extract_summary(result.content)
                prereq_context.append(f"- **{dep_step.title}**: {summary}")
            elif dep_step:
                prereq_context.append(f"- **{dep_step.title}** (not yet covered)")
        
        if prereq_context:
            return "**Prerequisites:**\n" + "\n".join(prereq_context)
        
        return ""
    
    def _extract_summary(self, content: str, max_sentences: int = 2) -> str:
        """
        Extract first few sentences from content as summary.
        Helps provide better context for subsequent topics.
        """
        # Remove markdown headers
        lines = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]
        
        if not lines:
            return "No content available"
        
        # Take first paragraph
        first_para = lines[0]
        
        # Split into sentences (simple approach)
        sentences = [s.strip() + '.' for s in first_para.split('.') if s.strip()]
        
        # Return first N sentences
        summary = ' '.join(sentences[:max_sentences])
        
        # Truncate if too long
        if len(summary) > 200:
            summary = summary[:197] + "..."
        
        return summary
    
    def _build_execution_prompt(
        self,
        state: AgentState,
        step: PlanStep,
        previous_context: str
    ) -> str:
        """Build prompt for topic content generation"""
        
        # Add original content context if available
        content_context = ""
        if state.original_content:
            # Extract relevant sections (simple keyword matching)
            keywords = step.title.lower().split()
            relevant_lines = []
            for line in state.original_content.split('\n')[:100]:  # First 100 lines
                if any(kw in line.lower() for kw in keywords):
                    relevant_lines.append(line)
            
            if relevant_lines:
                content_context = f"\n**Relevant excerpts from user materials:**\n" + \
                                 "\n".join(relevant_lines[:10]) + "\n"
        
        return f'''You are an expert educator for {state.subject}. Write structured study notes for a specific topic.

**Course Context:**
- Subject: {state.subject}
- Academic Level: {state.level}
- Exam Type: {state.exam_type}
{previous_context}

**Current Topic:**
- Title: {step.title}
- Coverage: {step.description}
- Target Length: {step.estimated_paragraphs} paragraphs
- Priority: {"Essential" if step.priority == 1 else "Important" if step.priority == 2 else "Advanced"}
{content_context}

**Requirements for Study Notes:**
1. Start with a clear definition/introduction
2. Structure content with subheadings
3. Include:
   - Key definitions and concepts
   - Formulas/theorems/facts (if applicable)
   - 1-2 examples or practice problems
   - Common mistakes and important notes
4. Write concisely - this is for quick review before exam
5. Use bullet points and numbered lists where appropriate
6. Do NOT duplicate content from other topics
7. Write in clear, student-friendly language

**Output Format:** Well-structured Markdown text ready for study.

Begin with topic content:'''
    
    async def execute_all(self, state: AgentState) -> Dict[int, StepResult]:
        """
        Execute all steps in plan sequentially with granular error handling.
        Continues execution even if some steps fail (partial success).
        
        Returns:
            Dictionary mapping step IDs to StepResult objects
        """
        from datetime import datetime
        
        results = {}
        state.status = ExecutionStatus.EXECUTING
        
        while not state.is_complete():
            current_step = state.get_current_step()
            step_start_time = datetime.utcnow()
            
            try:
                # Generate content for current step
                content = await self.execute_step(state)
                
                # Create successful result
                result = StepResult(
                    step_id=current_step.id,
                    content=content,
                    success=True,
                    timestamp=step_start_time.isoformat()
                )
                
                # Store result
                results[current_step.id] = result
                state.results[current_step.id] = result
                
            except Exception as e:
                # Log error but continue with next steps
                error_msg = f"Failed to generate topic '{current_step.title}': {str(e)}"
                state.log_error(error_msg)
                
                # Create failed result
                result = StepResult(
                    step_id=current_step.id,
                    content="",
                    success=False,
                    error_message=error_msg,
                    timestamp=step_start_time.isoformat()
                )
                
                results[current_step.id] = result
                state.results[current_step.id] = result
                state.failed_steps.append(current_step.id)
            
            finally:
                # Always move to next step
                state.current_step_index += 1
        
        # Update final status
        if not state.failed_steps:
            state.status = ExecutionStatus.COMPLETED
        elif state.has_successful_results():
            state.status = ExecutionStatus.PARTIALLY_COMPLETED
        else:
            state.status = ExecutionStatus.FAILED
        
        return results
    
    async def retry_failed_steps(self, state: AgentState) -> Dict[int, StepResult]:
        """
        Retry generation for failed steps.
        Allows users to continue after partial failure.
        
        Returns:
            Dictionary of retry results
        """
        from datetime import datetime
        
        retry_results = {}
        
        for step_id in state.failed_steps[:]:  # Copy list to avoid modification during iteration
            step = next((s for s in state.plan if s.id == step_id), None)
            if not step:
                continue
            
            try:
                # Temporarily set current step for context building
                original_index = state.current_step_index
                state.current_step_index = state.plan.index(step)
                
                # Retry generation
                content = await self.execute_step(state)
                
                # Update result
                result = StepResult(
                    step_id=step_id,
                    content=content,
                    success=True,
                    timestamp=datetime.utcnow().isoformat()
                )
                
                retry_results[step_id] = result
                state.results[step_id] = result
                state.failed_steps.remove(step_id)
                
                # Restore index
                state.current_step_index = original_index
                
            except Exception as e:
                state.log_error(f"Retry failed for '{step.title}': {str(e)}")
        
        # Update status if all retries succeeded
        if not state.failed_steps:
            state.status = ExecutionStatus.COMPLETED
        
        return retry_results
```

---

## 5.5 Finalizer - Assembly & Polish

### Step 5.5.1: Finalizer Implementation
```python
# backend/app/agent/finalizer.py
from app.agent.state import AgentState
from app.integrations.llm.base import LLMProvider


class NoteFinalizer:
    """
    Finalizer component: Assembles and polishes complete study notes.
    Makes ONE LLM call to finalize all content.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
    
    async def finalize(self, state: AgentState) -> str:
        """
        Assemble final study notes from all topic results.
        
        Args:
            state: AgentState with all execution results
        
        Returns:
            Complete, polished study notes
        """
        
        if not state.results:
            raise ValueError("No results to finalize")
        
        # Combine all topic content
        combined_notes = self._combine_topics(state)
        
        # Build finalization prompt
        prompt = self._build_finalization_prompt(state, combined_notes)
        
        # Call LLM for final polish
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.5,  # Moderate creativity
            max_tokens=8000,  # Larger limit for complete document
            system_prompt="You are an expert editor of educational materials."
        )
        
        # Track usage
        state.add_token_usage(
            response.tokens_input,
            response.tokens_output,
            response.cost_usd
        )
        
        return response.content.strip()
    
    def _combine_topics(self, state: AgentState) -> str:
        """
        Combine all successfully generated topic content in order.
        Handles partial completion gracefully.
        """
        
        sections = []
        skipped_topics = []
        
        for step in state.plan:
            result = state.results.get(step.id)
            
            if result and result.success and result.content:
                sections.append(f"## {step.title}\n\n{result.content}")
            else:
                # Track skipped topics
                error_note = result.error_message if result else "Not generated"
                skipped_topics.append(f"- {step.title}: {error_note}")
        
        combined = "\n\n---\n\n".join(sections)
        
        # Add note about skipped topics if any
        if skipped_topics:
            combined += "\n\n---\n\n## ⚠️ Incomplete Topics\n\n"
            combined += "The following topics could not be generated:\n\n"
            combined += "\n".join(skipped_topics)
        
        return combined
    
    def _build_finalization_prompt(self, state: AgentState, combined_notes: str) -> str:
        """Build prompt for final assembly and polish"""
        
        # Count total sections
        section_count = len([s for s in state.plan if s.id in state.results])
        
        return f'''You are an editor of educational materials. You have a draft of study notes for "{state.subject}".

**Your Task:**
1. Add a title page with:
   - Subject name
   - Exam type and academic level
   - Brief description (2-3 sentences)
2. Create Table of Contents with all {section_count} topics
3. Review and polish the content:
   - Remove any duplicate information
   - Ensure consistent terminology throughout
   - Add brief transitions between topics where needed
   - Fix formatting inconsistencies
4. Add a final section "Self-Check Questions" with 8-12 key questions covering all topics

**Important:**
- Do NOT change factual content
- Do NOT add new topics
- Do NOT remove existing topics
- Maintain the original structure and depth

**Draft Study Notes:**

{combined_notes}

**Output:** Complete, polished study notes in Markdown format, ready for exam preparation.'''
```

---

## 5.6 Orchestrator - Main Workflow

### Step 5.6.1: Orchestrator Implementation
```python
# backend/app/agent/orchestrator.py
from typing import Optional, Callable, Awaitable
from app.agent.state import AgentState
from app.agent.planner import CoursePlanner
from app.agent.executor import TopicExecutor
from app.agent.finalizer import NoteFinalizer
from app.integrations.llm.base import LLMProvider


ProgressCallback = Callable[[str, float], Awaitable[None]]


class PlanAndExecuteAgent:
    """
    Main orchestrator for Plan-and-Execute agent.
    Manages entire workflow: Plan → Execute → Finalize
    """
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider
        self.planner = CoursePlanner(llm_provider)
        self.executor = TopicExecutor(llm_provider)
        self.finalizer = NoteFinalizer(llm_provider)
    
    async def run(
        self,
        user_request: str,
        subject: str,
        exam_type: str,
        level: str,
        original_content: str = "",
        progress_callback: Optional[ProgressCallback] = None
    ) -> AgentState:
        """
        Execute complete agent workflow.
        
        Args:
            user_request: User's request for study notes
            subject: Subject name
            exam_type: Type of exam (oral, written, test)
            level: Academic level (school, bachelor, master, phd)
            original_content: Optional user-provided study materials
            progress_callback: Optional callback for progress updates
        
        Returns:
            Complete AgentState with final notes
        """
        
        # Initialize state
        state = AgentState(
            user_request=user_request,
            subject=subject,
            exam_type=exam_type,
            level=level,
            original_content=original_content
        )
        
        try:
            # Stage 1: Planning
            await self._notify_progress(progress_callback, "Planning structure...", 0.1)
            state.plan = await self.planner.make_plan(state)
            
            await self._notify_progress(
                progress_callback,
                f"Plan created: {len(state.plan)} topics",
                0.2
            )
            
            # Stage 2: Execution
            await self._notify_progress(progress_callback, "Generating content...", 0.3)
            
            while not state.is_complete():
                current_step = state.get_current_step()
                
                # Notify progress
                progress = 0.3 + (state.get_progress_percentage() * 0.5)  # 0.3 to 0.8
                await self._notify_progress(
                    progress_callback,
                    f"Generating: {current_step.title}",
                    progress
                )
                
                # Execute step
                content = await self.executor.execute_step(state)
                state.results[current_step.id] = content
                state.current_step_index += 1
            
            await self._notify_progress(progress_callback, "All topics generated", 0.8)
            
            # Stage 3: Finalization
            await self._notify_progress(progress_callback, "Assembling final notes...", 0.85)
            state.final_notes = await self.finalizer.finalize(state)
            
            await self._notify_progress(progress_callback, "Complete!", 1.0)
            
            return state
            
        except Exception as e:
            await self._notify_progress(
                progress_callback,
                f"Error: {str(e)}",
                state.get_progress_percentage()
            )
            raise
    
    async def _notify_progress(
        self,
        callback: Optional[ProgressCallback],
        message: str,
        progress: float
    ):
        """Notify progress via callback if provided"""
        if callback:
            await callback(message, progress)
```

---

## 5.7 Agent Service - Integration with Application

### Step 5.7.1: Agent Service
```python
# backend/app/services/agent_service.py
from uuid import UUID
from app.domain.exam import Exam
from app.domain.user import User
from app.repositories.exam_repository import ExamRepository
from app.repositories.topic_repository import TopicRepository
from app.agent.orchestrator import PlanAndExecuteAgent
from app.services.cost_guard_service import CostGuardService


class AgentService:
    """
    Service layer for AI agent integration.
    Connects agent to database and business logic.
    """
    
    def __init__(
        self,
        agent: PlanAndExecuteAgent,
        exam_repo: ExamRepository,
        topic_repo: TopicRepository,
        cost_guard: CostGuardService
    ):
        self.agent = agent
        self.exam_repo = exam_repo
        self.topic_repo = topic_repo
        self.cost_guard = cost_guard
    
    async def generate_exam_content(
        self,
        user: User,
        exam_id: UUID,
        progress_callback = None
    ) -> Exam:
        """
        Generate exam content using AI agent.
        
        Args:
            user: User requesting generation
            exam_id: Exam ID to generate content for
            progress_callback: Optional callback for progress updates
        
        Returns:
            Updated exam with generated content
        """
        
        # Get exam
        exam = await self.exam_repo.get_by_user_and_id(user.id, exam_id)
        if not exam:
            raise ValueError("Exam not found")
        
        if not exam.can_generate():
            raise ValueError(f"Cannot generate exam with status: {exam.status}")
        
        # Estimate cost
        estimated_tokens = len(exam.original_content) // 4
        estimated_cost = self.agent.llm.calculate_cost(
            estimated_tokens,
            estimated_tokens * 3  # Assume 3x output
        )
        
        # Check budget
        has_budget = await self.cost_guard.check_budget(user, estimated_cost)
        if not has_budget:
            raise ValueError("Insufficient budget for generation")
        
        # Mark as generating
        exam.start_generation()
        await self.exam_repo.update(exam)
        
        try:
            # Run agent
            state = await self.agent.run(
                user_request=f"Create study notes for {exam.title}",
                subject=exam.subject,
                exam_type=exam.exam_type,
                level=exam.level,
                original_content=exam.original_content,
                progress_callback=progress_callback
            )
            
            # Save results
            exam.mark_as_ready(
                ai_summary=state.final_notes,
                token_input=state.total_tokens_used // 2,  # Approximate
                token_output=state.total_tokens_used // 2,
                cost=state.total_cost_usd
            )
            
            # Save topics
            for i, plan_step in enumerate(state.plan):
                topic = Topic(
                    exam_id=exam.id,
                    user_id=user.id,
                    topic_name=plan_step.title,
                    content=state.results.get(plan_step.id, ""),
                    order_index=i,
                    difficulty_level=plan_step.priority.value
                )
                topic.estimate_study_time()
                await self.topic_repo.create(topic)
            
            exam.update_topic_count(len(state.plan))
            
            # Log usage
            await self.cost_guard.log_usage(
                user_id=user.id,
                model=self.agent.llm.get_model_name(),
                tokens_input=state.total_tokens_used // 2,
                tokens_output=state.total_tokens_used // 2,
                cost_usd=state.total_cost_usd,
                operation="exam_generation"
            )
            
            # Update exam
            updated = await self.exam_repo.update(exam)
            
            return updated
            
        except Exception as e:
            # Mark as failed
            exam.mark_as_failed()
            await self.exam_repo.update(exam)
            raise
```

---

## 5.8 Unit Tests for Agent

### Step 5.8.1: Test Planner
```python
# backend/tests/unit/agent/test_planner.py
import pytest
from unittest.mock import AsyncMock
from app.agent.planner import CoursePlanner
from app.agent.state import AgentState
from app.integrations.llm.base import LLMResponse


@pytest.mark.asyncio
class TestCoursePlanner:
    """Unit tests for CoursePlanner"""
    
    async def test_make_plan_success(self):
        """Test successful plan creation"""
        # Mock LLM response
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = LLMResponse(
            content='''[
                {
                    "id": 1,
                    "title": "Derivatives",
                    "description": "Basic derivative concepts",
                    "priority": 1,
                    "estimated_paragraphs": 5,
                    "dependencies": []
                }
            ]''',
            model="test",
            tokens_input=100,
            tokens_output=200,
            cost_usd=0.01,
            finish_reason="stop"
        )
        
        planner = CoursePlanner(mock_llm)
        state = AgentState(
            user_request="Test request",
            subject="Calculus",
            exam_type="written",
            level="bachelor"
        )
        
        plan = await planner.make_plan(state)
        
        assert len(plan) == 1
        assert plan[0].title == "Derivatives"
        assert state.total_tokens_used == 300
    
    async def test_make_plan_invalid_json(self):
        """Test error handling for invalid JSON"""
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = LLMResponse(
            content="Invalid JSON",
            model="test",
            tokens_input=10,
            tokens_output=10,
            cost_usd=0.001,
            finish_reason="stop"
        )
        
        planner = CoursePlanner(mock_llm)
        state = AgentState(
            user_request="Test",
            subject="Math",
            exam_type="written",
            level="bachelor"
        )
        
        with pytest.raises(ValueError, match="Failed to parse"):
            await planner.make_plan(state)
```

---

## 5.9 Best Practices & Next Steps

### Code Quality
- **Separation of concerns**: Each component has single responsibility
- **Async throughout**: All LLM calls are async
- **Error handling**: Specific exceptions for each failure mode
- **Progress tracking**: Callbacks for real-time updates

### Prompt Engineering
- **Specific instructions**: Clear, detailed prompts
- **Examples**: Include format examples in prompts
- **Low temperature for structure**: Use 0.3 for JSON generation
- **Higher temperature for content**: Use 0.7 for creative writing

### Testing
- Mock LLM responses with realistic fixtures
- Test error scenarios (invalid JSON, API failures)
- Test state transitions

### Next Steps
1. Implement all agent components
2. Create prompt templates library
3. Test with various subjects
4. Optimize token usage
5. Proceed to **Stage 6: API Layer**
