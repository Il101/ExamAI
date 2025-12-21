from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class TopicResponse(BaseModel):
    id: UUID
    exam_id: UUID
    topic_name: str
    content: Optional[str]
    content_blocknote: Optional[dict] = None  # BlockNote JSON format
    content_markdown_backup: Optional[str] = None  # Backup of original Markdown
    flashcard_count: int = 0
    status: str = "pending"  # pending, generating, ready, failed
    order_index: int
    difficulty_level: Optional[int] = None
    estimated_study_minutes: Optional[int] = None
    scheduled_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Progress tracking fields
    is_viewed: bool = False
    quiz_completed: bool = False
    last_viewed_at: Optional[datetime] = None
    
    # Navigation metadata (computed)
    prev_topic_id: Optional[UUID] = None
    next_topic_id: Optional[UUID] = None
    exam_title: Optional[str] = None

    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    topics: List[TopicResponse]

