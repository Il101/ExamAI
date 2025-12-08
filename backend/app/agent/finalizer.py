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
        # If cache is available, use it to ground the final summary and checks
        if state.cache_name:
            from app.core.config import settings
            try:
                # Use Gemini client directly for cached content
                # Add instruction to usage of cache
                prompt += "\n\n(Note: The original source document is available in your context. Use it to verify facts and improve the summary.)"
                
                response_obj = await self.llm.client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    config={
                        "cached_content": state.cache_name,
                    },
                    contents=[{
                        "role": "user", 
                        "parts": [{"text": "System: You are an expert editor of educational materials.\n\n" + prompt}]
                    }]
                )
                return response_obj.text.strip()
            except Exception as e:
                # Fallback to standard generation if cache fails
                print(f"[Finalizer] Cache usage failed: {e}. Falling back to standard generation.")
                pass

        # Standard generation (no cache or fallback)
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
        from app.prompts import load_prompt

        # Count total sections
        section_count = len([s for s in state.plan if s.id in state.results])

        # Load prompt template
        prompt = load_prompt(
            'finalizer/polish_content.txt',
            exam_type=state.exam_type,
            level=state.level,
            section_count=section_count,
            combined_notes=combined_notes
        )

        return prompt

