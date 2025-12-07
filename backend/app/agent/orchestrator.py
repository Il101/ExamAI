from datetime import datetime
from typing import Awaitable, Callable, Optional, List

from app.agent.cached_executor import CachedTopicExecutor
from app.agent.finalizer import NoteFinalizer
from app.agent.planner import CoursePlanner
from app.agent.state import AgentState, ExecutionStatus, StepResult, PlanStep
from app.integrations.llm.base import LLMProvider

ProgressCallback = Callable[[str, float], Awaitable[None]]


class PlanAndExecuteAgent:
    """
    Main orchestrator for Plan-and-Execute agent.
    Manages entire workflow: Plan → Execute → Finalize
    """

    def __init__(self, llm_provider: LLMProvider, max_topics: int | None = None):
        self.llm = llm_provider
        self.planner = CoursePlanner(llm_provider, max_topics=max_topics)
        self.executor = CachedTopicExecutor(llm_provider)
        self.finalizer = NoteFinalizer(llm_provider)

    async def run(
        self,
        user_request: str,
        subject: str,
        exam_type: str,
        level: str,
        original_content: str = "",
        existing_plan: Optional[List["PlanStep"]] = None,
        progress_callback: Optional[ProgressCallback] = None,
        on_step_complete: Optional[Callable[[StepResult], Awaitable[None]]] = None,
        cache_name: Optional[str] = None,
        exam_id: Optional[str] = None,
    ) -> AgentState:
        """
        Execute complete agent workflow.

        Args:
            user_request: User's request for study notes
            subject: Subject name
            exam_type: Type of exam (oral, written, test)
            level: Academic level (school, bachelor, master, phd)
            original_content: Optional user-provided study materials
            existing_plan: Optional pre-generated plan to execute
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
            original_content=original_content,
            cache_name=cache_name,
            exam_id=exam_id,
        )

        try:
            # Stage 1: Planning (or Loading Plan)
            state.status = ExecutionStatus.PLANNING
            
            if existing_plan:
                 await self._notify_progress(progress_callback, "Loading existing plan...", 0.1)
                 state.plan = existing_plan
                 await self._notify_progress(
                    progress_callback, f"Plan loaded: {len(state.plan)} topics", 0.2
                )
            else:
                await self._notify_progress(progress_callback, "Planning structure...", 0.1)
                state.plan = await self.planner.make_plan(state)
                await self._notify_progress(
                    progress_callback, f"Plan created: {len(state.plan)} topics", 0.2
                )

            # Stage 2: Execution
            state.status = ExecutionStatus.EXECUTING
            await self._notify_progress(progress_callback, "Generating content...", 0.3)

            while not state.is_complete():
                current_step = state.get_current_step()
                if not current_step:
                    break

                # Notify progress
                progress = 0.3 + (state.get_progress_percentage() * 0.5)  # 0.3 to 0.8
                await self._notify_progress(
                    progress_callback, f"Generating: {current_step.title}", progress
                )

                step_start_time = datetime.utcnow()
                
                # Retry logic for transient errors
                max_retries = 3
                retry_delay = 2
                success = False
                
                for attempt in range(max_retries + 1):
                    try:
                        # Execute step
                        content = await self.executor.execute_step(state)

                        # Create successful result
                        result = StepResult(
                            step_id=current_step.id,
                            content=content,
                            success=True,
                            timestamp=step_start_time.isoformat(),
                        )
                        state.results[current_step.id] = result
                        
                        # Notify completion
                        if on_step_complete:
                            await on_step_complete(result)

                        success = True
                        break # Success, exit retry loop

                    except Exception as e:
                        error_msg = str(e)
                        is_transient = "503" in error_msg or "429" in error_msg or "overloaded" in error_msg.lower()
                        
                        if attempt < max_retries and is_transient:
                            wait_time = retry_delay * (2 ** attempt) # Exponential backoff: 2, 4, 8
                            await self._notify_progress(
                                progress_callback, 
                                f"Topic '{current_step.title}' failed (attempt {attempt+1}/{max_retries+1}). Retrying in {wait_time}s...", 
                                progress
                            )
                            import asyncio
                            await asyncio.sleep(wait_time)
                            continue
                        
                        # Log error but continue with next steps if all retries failed
                        final_error_msg = (
                            f"Failed to generate topic '{current_step.title}' after {attempt+1} attempts: {error_msg}"
                        )
                        state.log_error(final_error_msg)

                        # Create failed result
                        result = StepResult(
                            step_id=current_step.id,
                            content="",
                            success=False,
                            error_message=final_error_msg,
                            timestamp=step_start_time.isoformat(),
                        )
                        state.results[current_step.id] = result
                        state.failed_steps.append(current_step.id)
                        break # Failed finally, exit retry loop

                state.current_step_index += 1

            await self._notify_progress(progress_callback, "All topics generated", 0.8)

            # Check if we can proceed to finalization
            if not state.has_successful_results():
                state.status = ExecutionStatus.FAILED
                raise ValueError("Failed to generate any topics. Cannot finalize.")

            # Stage 3: Finalization
            state.status = ExecutionStatus.FINALIZING
            await self._notify_progress(
                progress_callback, "Assembling final notes...", 0.85
            )
            state.final_notes = await self.finalizer.finalize(state)

            state.status = ExecutionStatus.COMPLETED
            await self._notify_progress(progress_callback, "Complete!", 1.0)

            return state

        except Exception as e:
            state.status = ExecutionStatus.FAILED
            state.log_error(f"Agent execution failed: {str(e)}")
            await self._notify_progress(
                progress_callback, f"Error: {str(e)}", state.get_progress_percentage()
            )
            raise

    async def _notify_progress(
        self, callback: Optional[ProgressCallback], message: str, progress: float
    ):
        """Notify progress via callback if provided"""
        if callback:
            await callback(message, progress)
