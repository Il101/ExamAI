from pydantic import BaseModel
from typing import Optional


class UpdateTopicContentRequest(BaseModel):
    """Request model for updating topic content"""
    content_blocknote: dict  # BlockNote JSON format
    content_markdown: Optional[str] = None  # Optional Markdown representation
