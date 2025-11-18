from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class TopicResponse(BaseModel):
    id: UUID
    exam_id: UUID
    title: str
    content: Optional[str]
    order: int
    
    class Config:
        from_attributes = True

class TopicListResponse(BaseModel):
    topics: List[TopicResponse]
