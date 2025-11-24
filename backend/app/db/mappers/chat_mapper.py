from app.db.models.chat import ChatMessageModel
from app.domain.chat import ChatMessage


class ChatMessageMapper:
    """Mapper between ChatMessage domain and ChatMessageModel"""

    @staticmethod
    def to_domain(model: ChatMessageModel) -> ChatMessage:
        """Convert database model to domain object"""
        return ChatMessage(
            id=model.id,
            user_id=model.user_id,
            topic_id=model.topic_id,
            role=model.role,
            content=model.content,
            tool_calls=model.tool_calls,
            created_at=model.created_at,
        )

    @staticmethod
    def to_model(domain: ChatMessage) -> ChatMessageModel:
        """Convert domain object to database model"""
        return ChatMessageModel(
            id=domain.id,
            user_id=domain.user_id,
            topic_id=domain.topic_id,
            role=domain.role,
            content=domain.content,
            tool_calls=domain.tool_calls,
            created_at=domain.created_at,
        )
