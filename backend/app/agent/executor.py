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

        # Call LLM with cache if available
        response = await self.llm.generate(
            prompt=prompt,
            temperature=0.7,  # Higher temperature for creative content
            max_tokens=2000,  # Limit per topic
            system_prompt="You are an expert educator writing study notes.",
            cache_name=state.cache_name,  # CRITICAL: Use cache to reduce input tokens
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
        from app.prompts import load_prompt

        # Prepare content section
        content_section = ""
        
        # If cache is active, DO NOT include raw content to avoid double token usage
        if state.cache_name:
            content_section = (
                "\n**Source Materials:**\n"
                "The full source content is already loaded in your context cache.\n"
                "Please refer to the cached documents to answer this request.\n"
            )
        elif state.original_content:
            # Extract relevant chunks based on keywords
            lines = state.original_content.split('\n')
            keywords = step.title.lower().split() + step.description.lower().split()
            # remove common words
            stop_words = {'and', 'the', 'of', 'in', 'to', 'a', 'for', 'on', 'with', 'generate', 'content', 'topic'}
            keywords = [k for k in keywords if k not in stop_words and len(k) > 3]
            
            relevant_content = []
            current_para = []
            
            for line in lines:
                if line.strip():
                    current_para.append(line)
                else:
                    if current_para:
                        para_text = " ".join(current_para)
                        if any(kw in para_text.lower() for kw in keywords):
                            relevant_content.append("\n".join(current_para))
                        current_para = []
            
            # Don't forget last paragraph
            if current_para:
                para_text = " ".join(current_para)
                if any(kw in para_text.lower() for kw in keywords):
                    relevant_content.append("\n".join(current_para))
            
            if relevant_content:
                # Provide top relevant paragraphs (up to 10 for better context)
                content_section = (
                    "\n**Relevant content from user's materials:**\n"
                    + "\n\n".join(relevant_content[:10])
                    + "\n"
                )
            else:
                # If no specific keyword matches, provide general context from entire file
                # Take samples from beginning, middle, and end
                total_lines = len(lines)
                sample_size = min(50, total_lines // 3)
                
                beginning = "\n".join(lines[:sample_size])
                middle_start = (total_lines - sample_size) // 2
                middle = "\n".join(lines[middle_start:middle_start + sample_size])
                end = "\n".join(lines[-sample_size:])
                
                content_section = (
                    "\n**User's study materials (sampled from entire file):**\n"
                    + f"\n[Beginning]\n{beginning}\n\n"
                    + f"[Middle]\n{middle}\n\n"
                    + f"[End]\n{end}\n"
                )

        # Load prompt template and substitute variables
        prompt = load_prompt(
            'executor/topic_content.txt',
            level=state.level,
            exam_type=state.exam_type,
            previous_context=previous_context,
            title=step.title,
            description=step.description,
            estimated_paragraphs=step.estimated_paragraphs,
            content_section=content_section
        )

        return prompt

    async def execute_all_steps_with_recovery(
        self, state: AgentState
    ) -> dict[str, StepResult]:
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
