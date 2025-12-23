import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field

from app.core.config import settings
from app.agent.state import AgentState, ExecutionStatus, PlanStep, StepResult
from app.agent.schemas import ReflectionResult
from app.integrations.llm.base import LLMProvider

logger = logging.getLogger(__name__)


class TopicSchema(BaseModel):
    """Schema for a single topic content"""
    id: str = Field(..., description="The EXACT ID string from the provided topics list")
    title: str = Field(..., description="Topic title")
    overview: str = Field(..., description="High-level overview (1 paragraph)")
    key_concepts: List[str] = Field(..., description="List of 3-5 key scientific concepts")
    detailed_content: str = Field(..., description="Main educational content (markdown formatted)")
    summary: str = Field(..., description="Final wrap-up summary")


class TopicBatchSchema(BaseModel):
    """Schema for a batch of topics"""
    topics: List[TopicSchema] = Field(..., description="List of generated topics")


class TopicExecutor:
    """
    Executor component: Generates content for individual topics.
    Makes N LLM calls (one per topic in plan).
    """

    def __init__(self, llm_provider: LLMProvider):
        self.llm = llm_provider

    async def execute_step(self, state: AgentState, max_retries: int = 2) -> str:
        """
        Generate content for current step with retry logic.

        Args:
            state: AgentState with plan and current step index
            max_retries: Maximum number of retry attempts (reduced to 2 to prevent cascade)

        Returns:
            Generated content for the topic
        """

        current_step = state.get_current_step()
        if not current_step:
            raise ValueError("No current step to execute")

        print(
            f"[Executor] Generating content for topic {current_step.id}: '{current_step.title}' using model: {settings.GEMINI_MODEL}..."
        )

        # Build context from previous results
        previous_context = self._build_previous_context(state, current_step)

        # Build execution prompt
        prompt = self._build_execution_prompt(state, current_step, previous_context)

        # Retry loop for transient failures
        last_error = None
        for attempt in range(max_retries):
            try:
                output_language = getattr(state, "output_language", "ru") or "ru"
                output_language_lower = str(output_language).lower()
                if output_language_lower.startswith("ru"):
                    language_name = "Russian"
                elif output_language_lower.startswith("en"):
                    language_name = "English"
                else:
                    language_name = str(output_language)

                # Dynamic output budget: the topic template is fairly structured
                # (many sections), so 2000 tokens is often too small and leads
                # to truncated topics.
                estimated_sections = getattr(current_step, "estimated_paragraphs", 5) or 5
                max_tokens = min(8000, max(4000, 2500 + int(estimated_sections) * 700))
                if attempt > 0:
                    # On retries, increase output budget to avoid repeated truncation.
                    max_tokens = min(12000, int(max_tokens * (1.6 ** attempt)))

                # Call LLM with structured output
                response = await self.llm.generate(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=max_tokens,
                    system_prompt=(
                        f"You are an expert educator writing study notes in {language_name}. "
                        "Always return structured JSON based on the provided schema."
                    ),
                    response_schema=TopicSchema,
                    cache_name=state.cache_name,
                    operation_type="topic_generation"
                )

                print(
                    f"[Executor] Content generated for topic {current_step.id}. Tokens: {response.tokens_input}/{response.tokens_output}"
                )

                # If the model stopped due to output length, retry with a larger budget.
                finish_reason = (response.finish_reason or "").lower()
                if finish_reason in {"max_tokens", "length", "max_output_tokens"}:
                    print(
                        f"[Executor] ⚠️ Topic {current_step.id} likely truncated (finish_reason={finish_reason}). "
                        f"Retrying with higher max_tokens..."
                    )
                    if attempt < max_retries - 1:
                        continue

                # Track usage
                state.add_token_usage(
                    response.tokens_input, response.tokens_output, response.cost_usd
                )

                # Use parsed content if available
                if response.parsed:
                    topic_data: TopicSchema = response.parsed
                    # Format as markdown for backwards compatibility with the UI
                    content = (
                        f"### {topic_data.title}\n\n"
                        f"#### Ключевые понятия\n" + "\n".join([f"- {c}" for c in topic_data.key_concepts]) + "\n\n"
                        f"#### Детальное объяснение\n"
                        f"{topic_data.overview}\n\n"
                        f"{topic_data.detailed_content}\n\n"
                        f"#### Резюме\n{topic_data.summary}"
                    )
                else:
                    # Fallback to text cleaning
                    from app.utils.content_cleaner import strip_thinking_tags
                    content = strip_thinking_tags(response.content).strip()

                # --- REFLECTION STEP (NEW) ---
                if state.cache_name:
                    try:
                        reflection = await self._reflect_on_content(state, current_step, content)
                        
                        if not reflection.is_accurate or not reflection.pedagogical_alignment:
                            issue_type = "Accuracy/Hallucination" if not reflection.is_accurate else "Pedagogical Alignment"
                            print(f"[Executor] ⚠️ Reflection failed ({issue_type}) for '{current_step.title}'. Errors: {reflection.hallucinations + reflection.errors}")
                            print(f"[Executor] 🔄 Attempting self-correction with suggestions: {reflection.suggestions}")
                            
                            # Self-correction prompt
                            correction_prompt = (
                                f"{prompt}\n\n"
                                f"--- \n"
                                f"⚠️ **SELF-CORRECTION REQUIRED** ⚠️\n"
                                f"Your previous output contained issues:\n"
                                + "\n".join([f"- {e}" for e in reflection.errors + reflection.hallucinations]) +
                                (f"\n- Pedagogical Alignment issues found." if not reflection.pedagogical_alignment else "") +
                                f"\n\n**CRITICAL INSTRUCTIONS FOR FIXING (STRICT GROUNDING):**\n{reflection.suggestions}\n"
                                f"Please regenerate the topic content based strictly on the source materials, matching the level and fixing these issues."
                            )
                            
                            # Regenerate with correction instructions
                            correction_response = await self.llm.generate(
                                prompt=correction_prompt,
                                temperature=0.5, # Lower temperature for better accuracy during correction
                                max_tokens=max_tokens,
                                system_prompt=f"You are an expert educator. FIX the mistakes noted in the reflection. Use {language_name}.",
                                response_schema=TopicSchema,
                                cache_name=state.cache_name,
                                operation_type="topic_correction"
                            )
                            
                            state.add_token_usage(correction_response.tokens_input, correction_response.tokens_output, correction_response.cost_usd)
                            
                            if correction_response.parsed:
                                td = correction_response.parsed
                                content = (
                                    f"### {td.title}\n\n"
                                    f"#### Ключевые понятия\n" + "\n".join([f"- {c}" for c in td.key_concepts]) + "\n\n"
                                    f"#### Детальное объяснение\n"
                                    f"{td.overview}\n\n"
                                    f"{td.detailed_content}\n\n"
                                    f"#### Резюме\n{td.summary}"
                                )
                                print(f"[Executor] ✅ Self-correction successful for '{current_step.title}'")
                            else:
                                print(f"[Executor] ⚠️ Self-correction failed to return parsed JSON for '{current_step.title}', using uncorrected content.")
                        else:
                            print(f"[Executor] ✅ Reflection passed for '{current_step.title}'")
                    except Exception as re:
                        print(f"[Executor] ⚠️ Reflection/Correction step failed: {re}. Continuing with original content.")

                return content

            except RuntimeError as e:
                last_error = e
                error_msg = str(e)
                
                # Check if it's a transient error (timeout, service unavailable, rate limit)
                is_transient = (
                    "timed out" in error_msg.lower() or 
                    "timeout" in error_msg.lower() or
                    "503" in error_msg or
                    "429" in error_msg or
                    "overloaded" in error_msg or
                    "resource exhausted" in error_msg or
                    "service unavailable" in error_msg
                )

                if is_transient:
                    print(f"[Executor] ⚠️ Attempt {attempt + 1}/{max_retries} failed with transient error: {error_msg}")
                    
                    if attempt < max_retries - 1:
                        # Reduced backoff: 2s, 4s (was 5s, 10s, 20s)
                        # SDK already retried, so we just need short app-level retry
                        wait_time = 2 * (2 ** attempt)
                        print(f"[Executor] Retrying in {wait_time}s...")
                        import asyncio
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"[Executor] ❌ All {max_retries} attempts failed for topic {current_step.id}")
                        raise RuntimeError(f"Failed to generate topic after {max_retries} attempts: {error_msg}")
                else:
                    # Non-timeout error, don't retry
                    raise

        # Should never reach here, but just in case
        raise last_error if last_error else RuntimeError("Unknown error in execute_step")

    async def _reflect_on_content(self, state: AgentState, step: PlanStep, content: str) -> ReflectionResult:
        """
        Call Reflector Agent to verify generated content against source.
        """
        from app.prompts import load_prompt
        
        source_context = (
            "The full source material for this course is loaded in your context cache. "
            "Refer to the cached PDF/document to verify the accuracy of the generated content."
        )
        
        reflection_prompt = load_prompt(
            'executor/reflection.txt',
            title=step.title,
            generated_content=content,
            source_context=source_context
        )
        
        response = await self.llm.generate(
            prompt=reflection_prompt,
            temperature=0.1,  # Ultra-low temperature for factual verification
            max_tokens=2000,
            system_prompt="You are a strict fact-checker. Verify generated content against cached source.",
            response_schema=ReflectionResult,
            cache_name=state.cache_name,
            operation_type="topic_reflection"
        )
        
        state.add_token_usage(response.tokens_input, response.tokens_output, response.cost_usd)
        
        if response.parsed:
            return response.parsed
        
        raise RuntimeError("Failed to parse reflection result")

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
        if len(summary) > 500:
            summary = summary[:497] + "..."

        return summary

    def _build_execution_prompt(
        self, state: AgentState, step: PlanStep, previous_context: str
    ) -> str:
        """Build prompt for topic content generation"""
        from app.prompts import load_prompt

        output_language = getattr(state, "output_language", "ru") or "ru"
        output_language_lower = str(output_language).lower()
        if output_language_lower.startswith("ru"):
            output_language_label = "Russian"
        elif output_language_lower.startswith("en"):
            output_language_label = "English"
        else:
            output_language_label = str(output_language)

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
            output_language=output_language_label,
            level=state.level,
            exam_type=state.exam_type,
            previous_context=previous_context,
            title=step.title,
            description=step.description,
            estimated_paragraphs=step.estimated_paragraphs,
            content_section=content_section
        )
        
        # DEBUG: Trace prompt size issues
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"[DEBUG_TRACE] Building Prompt for {step.id}: "
            f"CacheName={state.cache_name}, "
            f"ContentSectionLen={len(content_section)}, "
            f"PromptLen={len(prompt)}, "
            f"PreviousContextLen={len(previous_context)}"
        )

        return prompt

    async def execute_batch(self, state: AgentState, steps: List[PlanStep], max_retries: int = 2) -> Dict[int, str]:
        """
        Execute a batch of topics in a single LLM call.
        """
        if not steps:
            return {}

        topic_ids = [s.id for s in steps]
        print(f"[Executor] Generating BATCH for topics {topic_ids}: {[s.title for s in steps]} using model: {settings.GEMINI_MODEL}...")

        # Build context from previous results (using the first step's context as base)
        previous_context = self._build_previous_context(state, steps[0])

        # Form topics list for prompt
        topics_list = "\n".join([f"- {s.id}: {s.title} ({s.description})" for s in steps])

        # Prepare content section (using cache strategy from execute_step)
        content_section = ""
        if state.cache_name:
            content_section = (
                "\n**Source Materials:**\n"
                "The full source content is already loaded in your context cache.\n"
                "Please refer to the cached documents to answer this request.\n"
            )
        else:
            # For simplicity in batching, if no cache, we'd need a more complex strategy.
            # But in the optimized flow, cache is almost always present.
            content_section = "Refer to the provided materials."

        from app.prompts import load_prompt
        output_language = getattr(state, "output_language", "ru") or "ru"
        
        prompt = load_prompt(
            'executor/topic_batch.txt',
            output_language=output_language,
            level=state.level,
            exam_type=state.exam_type,
            previous_context=previous_context,
            topics_list=topics_list,
            content_section=content_section
        )

        last_error = None
        for attempt in range(max_retries):
            try:
                # Dynamic budget for batch (increased to 20k to accommodate detailed pedagogical content)
                max_tokens = min(20000, 8000 + len(steps) * 2000)
                if attempt > 0:
                    max_tokens = min(25000, int(max_tokens * (1.5 ** attempt)))
                
                response = await self.llm.generate(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=max_tokens,
                    system_prompt=f"You are an expert educator. Return structured JSON for {len(steps)} topics.",
                    response_schema=TopicBatchSchema,
                    cache_name=state.cache_name,
                    operation_type="topic_batch_generation"
                )

                # Check for truncation
                finish_reason = (response.finish_reason or "").lower()
                if finish_reason in {"max_tokens", "length", "max_output_tokens"}:
                    logger.warning(f"Batch generation likely truncated (finish_reason={finish_reason}). Retrying with higher max_tokens...")
                    if attempt < max_retries - 1:
                        continue

                # Track usage
                state.add_token_usage(response.tokens_input, response.tokens_output, response.cost_usd)

                if response.parsed:
                    batch_data: TopicBatchSchema = response.parsed
                    results_map = {}
                    for t in batch_data.topics:
                        formatted_content = (
                            f"### {t.title}\n\n"
                            f"#### Ключевые понятия\n" + "\n".join([f"- {c}" for c in t.key_concepts]) + "\n\n"
                            f"#### Детальное объяснение\n"
                            f"{t.overview}\n\n"
                            f"{t.detailed_content}\n\n"
                            f"#### Резюме\n{t.summary}"
                        )
                        
                        # VERIFICATION LAYER: Check each topic in batch
                        is_valid = True
                        if state.cache_name:
                            try:
                                # Find corresponding PlanStep for this topic
                                step_match = next((s for s in steps if str(s.id) == str(t.id)), None)
                                if step_match:
                                    reflection = await self._reflect_on_content(state, step_match, formatted_content)
                                    if not reflection.is_accurate or not reflection.pedagogical_alignment:
                                        issue_type = "Accuracy" if not reflection.is_accurate else "Pedagogy"
                                        logger.warning(f"[Executor] Batch verification failed ({issue_type}) for topic {t.id}: {t.title}")
                                        is_valid = False
                            except Exception as re:
                                logger.error(f"[Executor] Batch reflection error for topic {t.id}: {re}")
                        
                        if is_valid:
                            # Normalize returned ID to string for lookup
                            results_map[str(t.id)] = formatted_content
                    
                    # Check if any topics are missing from response (either LLM forgot or verification failed)
                    for step in steps:
                        # Normalize step ID to string for lookup
                        step_id_str = str(step.id)
                        if step_id_str not in results_map:
                            logger.warning(f"Topic {step_id_str} ({step.title}) not available (failed gen or verification), retrying individually later.")
                    
                    return results_map

            except Exception as e:
                last_error = e
                logger.warning(f"Batch attempt {attempt+1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
        
        raise last_error or RuntimeError("Batch generation failed")

    async def execute_all_steps_with_recovery(
        self, state: AgentState, batch_size: int = 4
    ) -> dict[str, StepResult]:
        """
        Execute all steps in plan using BATCHING to save costs.
        """
        results = {}
        state.status = ExecutionStatus.EXECUTING
        
        # Split plan into batches
        plan_steps = state.plan[state.current_step_index:]
        batches = [plan_steps[i : i + batch_size] for i in range(0, len(plan_steps), batch_size)]

        for batch in batches:
            batch_start_time = datetime.utcnow()
            try:
                # Try batch execution
                batch_results = await self.execute_batch(state, batch)
                
                for step in batch:
                    step_id_str = str(step.id)
                    if step_id_str in batch_results:
                        result = StepResult(
                            step_id=step.id,
                            content=batch_results[step_id_str],
                            success=True,
                            tokens_used=0, # Per-step tokens approximated as 0 since tracked in batch
                            cost_usd=0,
                            timestamp=batch_start_time.isoformat(),
                        )
                        results[step_id_str] = result
                        state.results[step.id] = result
                        state.current_step_index += 1
                    else:
                        # If a specific step failed in batch, retry individually
                        try:
                            content = await self.execute_step(state) # state.current_step_index points here
                            result = StepResult(step_id=step.id, content=content, success=True, timestamp=datetime.utcnow().isoformat())
                            results[step.id] = result
                            state.results[step.id] = result
                        except Exception as e:
                            error_msg = f"Failed individual retry for {step.title}: {e}"
                            state.log_error(error_msg)
                            state.results[step.id] = StepResult(step_id=step.id, content="", success=False, error_message=error_msg)
                            state.failed_steps.append(step.id)
                        finally:
                            state.current_step_index += 1

            except Exception as e:
                logger.error(f"Batch execution failed: {e}. Falling back to individual generation.")
                # Fallback to individual for this whole batch
                for step in batch:
                    try:
                        content = await self.execute_step(state)
                        results[step.id] = StepResult(step_id=step.id, content=content, success=True, timestamp=datetime.utcnow().isoformat())
                        state.results[step.id] = results[step.id]
                    except Exception as ex:
                        error_msg = f"Individual fallback failed for {step.title}: {ex}"
                        state.log_error(error_msg)
                        state.results[step.id] = StepResult(step_id=step.id, content="", success=False, error_message=error_msg)
                        state.failed_steps.append(step.id)
                    finally:
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
                    tokens_used=state.total_tokens_used,
                    tokens_input=state.total_tokens_input,
                    tokens_output=state.total_tokens_output,
                    cost_usd=state.total_cost_usd,
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
