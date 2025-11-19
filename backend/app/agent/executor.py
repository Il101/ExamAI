from datetime import datetime
from typing import Dict

from app.agent.state import AgentState, ExecutionStatus, PlanStep, StepResult
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

        print(
            f"[Executor] Generating content for topic {current_step.id}: '{current_step.title}'..."
        )

        # Build context from previous results
        previous_context = self._build_previous_context(state, current_step)

        # Build execution prompt
        prompt = self._build_execution_prompt(state, current_step, previous_context)

        # Call LLM
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.7,  # Higher temperature for creative content
            max_tokens=2000,  # Limit per topic
            system_prompt="You are an expert educator writing study notes.",
        )

        print(
            f"[Executor] Content generated for topic {current_step.id}. Tokens: {response.tokens_input}/{response.tokens_output}"
        )

        # Track usage
        state.add_token_usage(
            response.tokens_input, response.tokens_output, response.cost_usd
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
        lines = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        ]

        if not lines:
            return "No content available"

        # Take first paragraph
        first_para = lines[0]

        # Split into sentences (simple approach)
        sentences = [s.strip() + "." for s in first_para.split(".") if s.strip()]

        # Return first N sentences
        summary = " ".join(sentences[:max_sentences])

        # Truncate if too long
        if len(summary) > 200:
            summary = summary[:197] + "..."

        return summary

    def _build_execution_prompt(
        self, state: AgentState, step: PlanStep, previous_context: str
    ) -> str:
        """Build prompt for topic content generation"""

        # Add original content context if available
        content_context = ""
        if state.original_content:
            # Extract relevant sections (simple keyword matching)
            keywords = step.title.lower().split()
            relevant_lines = []
            for line in state.original_content.split("\n")[:100]:  # First 100 lines
                if any(kw in line.lower() for kw in keywords):
                    relevant_lines.append(line)

            if relevant_lines:
                content_context = (
                    "\\n**Relevant excerpts from user materials:**\\n"
                    + "\\n".join(relevant_lines[:10])
                    + "\\n"
                )

        return f"""You are an expert educator for {state.subject}. Write structured study notes for a specific topic.

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

Begin with topic content:"""

    async def execute_all(self, state: AgentState) -> Dict[int, StepResult]:
        """
        Execute all steps in plan sequentially with granular error handling.
        Continues execution even if some steps fail (partial success).

        Returns:
            Dictionary mapping step IDs to StepResult objects
        """

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
                    timestamp=step_start_time.isoformat(),
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
                    timestamp=step_start_time.isoformat(),
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

        retry_results = {}

        for step_id in state.failed_steps[
            :
        ]:  # Copy list to avoid modification during iteration
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
                    timestamp=datetime.utcnow().isoformat(),
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
