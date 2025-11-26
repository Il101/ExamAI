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
            system_prompt="You are an expert editor of educational materials.",
        )

        # Track usage
        state.add_token_usage(
            response.tokens_input, response.tokens_output, response.cost_usd
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

        return f"""You are an editor of educational materials. Polish the study notes below into a professional document.

**CRITICAL:** The course title may be generic or misleading - focus on the ACTUAL CONTENT of the materials.

**Your Task:**
1. Add a professional title page with:
   - **AI Summary** heading
   - Subject: Infer from content (ignore generic title)
   - Exam Type: {state.exam_type}
   - Academic Level: {state.level}
   - Brief description (2-3 sentences about ACTUAL content)
2. Create Table of Contents with all {section_count} topics
3. Polish the formatting:
   - Ensure consistent heading levels
   - Add proper spacing between sections
   - Make sure lists are properly formatted
   - Verify tables render correctly
   - Add horizontal rules between major sections
4. Review content quality:
   - Remove any placeholder text `[Insert X]`
   - Remove duplicate information
   - Ensure terminology is consistent
   - Add smooth transitions between topics
5. Add final section with 10-12 self-check questions covering all topics

**FORMATTING GUIDELINES:**
- Use `###` for topic headings
- Use `-` for bullet lists
- Use `1.` for numbered lists
- Use tables for comparisons
- Keep paragraphs SHORT (2-4 sentences)
- Use **bold** for key terms
- Use `>` blockquotes for important notes

**Important:**
- Do NOT change factual content
- Do NOT add new topics or remove existing ones
- Do NOT use placeholder text
- Make it scannable and easy to review quickly

**Draft Study Notes:**

{combined_notes}

**Output:** Complete, professionally formatted study notes in Markdown."""
