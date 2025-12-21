# backend/app/domain/exam.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal, Optional
from uuid import UUID, uuid4

ExamStatus = Literal["draft", "planning", "planned", "generating", "ready", "failed", "archived"]
ExamType = Literal["oral", "written", "test"]
ExamLevel = Literal["school", "bachelor", "master", "phd"]


@dataclass
class Exam:
    """
    Exam domain entity.
    Represents a study material with AI-generated content.
    """

    user_id: UUID = field(default_factory=uuid4)
    course_id: Optional[UUID] = None

    # Basic info
    title: str = ""
    subject: str = ""
    exam_type: ExamType = "written"
    level: ExamLevel = "bachelor"

    # Content
    original_content: str = ""  # User-provided material
    ai_summary: Optional[str] = None  # Generated summary
    original_file_url: Optional[str] = None  # URL of uploaded file in storage
    original_file_mime_type: Optional[str] = None  # MIME type of uploaded file
    
    # V3.0 Cache fields
    cache_name: Optional[str] = None  # Gemini cache identifier
    storage_path: Optional[str] = None  # S3/Supabase storage path
    plan_data: Optional[dict] = None  # ExamPlan JSON
    cache_expires_at: Optional[datetime] = None  # Cache expiry timestamp

    # Metadata
    status: ExamStatus = "draft"
    plan_ready_at: Optional[datetime] = None  # When plan was created
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # AI usage tracking
    token_count_input: int = 0
    token_count_output: int = 0
    generation_cost_usd: float = 0.0

    # Topics (will be populated by Agent)
    topic_count: int = 0
    completed_topics: int = 0
    due_flashcards_count: int = 0
    total_actual_study_minutes: int = 0
    total_planned_study_minutes: int = 0
    average_difficulty: float = 0.0

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate exam data"""
        if not self.title or len(self.title.strip()) < 3:
            raise ValueError("Title must be at least 3 characters")

        if not self.subject or len(self.subject.strip()) < 2:
            raise ValueError("Subject must be at least 2 characters")

        if self.status == "ready" and not self.ai_summary:
            raise ValueError("Ready exam must have AI summary")

    # Business logic

    def can_create_plan(self) -> bool:
        """Check if exam can start plan creation"""
        return self.status == "draft" and len(self.original_content) >= 100
    
    def start_planning(self):
        """Mark exam as planning (plan creation task started)"""
        if not self.can_create_plan():
            raise ValueError(f"Cannot start planning: status={self.status}")
        self.status = "planning"
        self.updated_at = datetime.now(timezone.utc)
    
    def can_generate(self) -> bool:
        """Check if exam can start content generation"""
        return self.status in ["planned", "failed"] and self.topic_count > 0

    def mark_as_planned(self):
        """Mark exam as planned (topics created, ready for generation)"""
        if self.status != "planning":
            raise ValueError(f"Cannot mark as planned: status={self.status}")
        
        self.status = "planned"
        self.plan_ready_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def start_generation(self):
        """Mark exam as generating content"""
        if not self.can_generate():
            raise ValueError(f"Cannot start generation: status={self.status}")
        self.status = "generating"
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_ready(
        self, ai_summary: str, token_input: int, token_output: int, cost: float
    ):
        """Mark exam as successfully generated"""
        if self.status != "generating":
            raise ValueError("Can only mark generating exams as ready")

        self.ai_summary = ai_summary
        self.token_count_input = token_input
        self.token_count_output = token_output
        self.generation_cost_usd = cost
        self.status = "ready"
        self.updated_at = datetime.now(timezone.utc)

    def mark_as_failed(self):
        """Mark exam generation as failed (idempotent)"""
        # Allow marking as failed from planning, planned, generating, or already failed
        if self.status not in ["planning", "planned", "generating", "failed"]:
            raise ValueError(f"Cannot mark as failed: status={self.status}")
        
        # Idempotent - if already failed, just update timestamp
        self.status = "failed"
        self.updated_at = datetime.now(timezone.utc)

    def archive(self):
        """Archive exam"""
        if self.status == "generating":
            raise ValueError("Cannot archive exam during generation")

        self.status = "archived"
        self.updated_at = datetime.now(timezone.utc)

    def get_estimated_tokens(self) -> int:
        """Estimate tokens for generation (rough: 1 token ≈ 4 chars)"""
        return len(self.original_content) // 4

    def update_topic_count(self, count: int):
        """Update number of generated topics"""
        if count < 0:
            raise ValueError("Topic count cannot be negative")
        self.topic_count = count
        self.updated_at = datetime.now(timezone.utc)
