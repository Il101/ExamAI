from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, List, Dict, Any
from uuid import UUID, uuid4


@dataclass
class ChatMessage:
    """
    Chat message between user and AI tutor.
    Supports Function Calling tool usage tracking.
    """

    id: UUID = field(default_factory=uuid4)
    user_id: UUID = field(default_factory=uuid4)
    topic_id: UUID = field(default_factory=uuid4)
    
    role: Literal["user", "assistant"] = "user"
    content: str = ""
    
    # Function Calling metadata
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        self._validate()

    def _validate(self):
        """Validate chat message"""
        if not self.content or len(self.content.strip()) < 1:
            raise ValueError("Message content cannot be empty")
        
        if self.role not in ["user", "assistant"]:
            raise ValueError("Role must be 'user' or 'assistant'")
