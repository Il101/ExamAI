from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class Priority(int, Enum):
    """Priority levels for plan steps"""

    HIGH = 1  # Must-have topics
    MEDIUM = 2  # Important topics
    LOW = 3  # Optional/advanced topics


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
    output_language: str = "ru"  # Preferred output language (e.g., "ru", "en")
    original_content: str = ""  # User-provided study materials (optional)
    cache_name: Optional[str] = None  # Gemini cache name (optional)
    exam_id: Optional[str] = None  # Exam ID for fallback (optional)

    # Execution state
    plan: List[PlanStep] = field(default_factory=list)
    current_step_index: int = 0
    results: Dict[int, StepResult] = field(
        default_factory=dict
    )  # step_id -> result with metadata
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
        timestamp = datetime.utcnow().isoformat()
        self.error_log.append(f"[{timestamp}] {error}")

    def add_token_usage(self, tokens_input: int, tokens_output: int, cost: float):
        """Track token usage and costs"""
        self.total_tokens_used += tokens_input + tokens_output
        self.total_cost_usd += cost
