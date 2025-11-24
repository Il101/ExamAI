from typing import List
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.mappers.chat_mapper import ChatMessageMapper
from app.db.models.chat import ChatMessageModel
from app.domain.chat import ChatMessage
from app.repositories.base import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage, ChatMessageModel]):
    """Repository for ChatMessage entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ChatMessageModel, ChatMessageMapper)

    async def list_by_topic(
        self, topic_id: UUID, limit: int = 50
    ) -> List[ChatMessage]:
        """
        Get chat history for a topic.
        
        Args:
            topic_id: Topic ID
            limit: Maximum number of messages to return
            
        Returns:
            List of chat messages, ordered by creation time (oldest first)
        """
        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.topic_id == topic_id)
            .order_by(ChatMessageModel.created_at.asc())
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        models = result.scalars().all()

        return [self.mapper.to_domain(model) for model in models]

    async def delete_by_topic(self, topic_id: UUID) -> int:
        """
        Delete all messages for a topic.
        
        Args:
            topic_id: Topic ID
            
        Returns:
            Number of deleted messages
        """
        stmt = select(ChatMessageModel).where(ChatMessageModel.topic_id == topic_id)
        result = await self.session.execute(stmt)
        messages = result.scalars().all()
        
        count = len(messages)
        for message in messages:
            await self.session.delete(message)
        
        await self.session.commit()
        return count
