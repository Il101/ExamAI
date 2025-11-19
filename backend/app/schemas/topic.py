from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class TopicResponse(BaseModel):
    id: UUID
    exam_id: UUID
    topic_name: str
    content: Optional[str]
    order_index: int
    difficulty_level: Optional[int] = None
    estimated_study_minutes: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TopicListResponse(BaseModel):
    topics: List[TopicResponse]
