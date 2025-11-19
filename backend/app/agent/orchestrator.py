from typing import Optional, Callable, Awaitable
from datetime import datetime
from app.agent.state import AgentState, StepResult, ExecutionStatus
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
    
    def __init__(self, llm_provider: LLMProvider, max_topics: int | None = None):
        self.llm = llm_provider
        self.planner = CoursePlanner(llm_provider, max_topics=max_topics)
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
            state.status = ExecutionStatus.PLANNING
            await self._notify_progress(progress_callback, "Planning structure...", 0.1)
            state.plan = await self.planner.make_plan(state)
            
            await self._notify_progress(
                progress_callback,
                f"Plan created: {len(state.plan)} topics",
                0.2
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
                    progress_callback,
                    f"Generating: {current_step.title}",
                    progress
                )
                
                step_start_time = datetime.utcnow()
                try:
                    # Execute step
                    content = await self.executor.execute_step(state)
                    
                    # Create successful result
                    result = StepResult(
                        step_id=current_step.id,
                        content=content,
                        success=True,
                        timestamp=step_start_time.isoformat()
                    )
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
                    state.results[current_step.id] = result
                    state.failed_steps.append(current_step.id)
                
                finally:
                    state.current_step_index += 1
            
            await self._notify_progress(progress_callback, "All topics generated", 0.8)
            
            # Check if we can proceed to finalization
            if not state.has_successful_results():
                state.status = ExecutionStatus.FAILED
                raise ValueError("Failed to generate any topics. Cannot finalize.")
            
            # Stage 3: Finalization
            state.status = ExecutionStatus.FINALIZING
            await self._notify_progress(progress_callback, "Assembling final notes...", 0.85)
            state.final_notes = await self.finalizer.finalize(state)
            
            state.status = ExecutionStatus.COMPLETED
            await self._notify_progress(progress_callback, "Complete!", 1.0)
            
            return state
            
        except Exception as e:
            state.status = ExecutionStatus.FAILED
            state.log_error(f"Agent execution failed: {str(e)}")
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
