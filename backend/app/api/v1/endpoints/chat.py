from typing import List
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.dependencies import get_current_user
from app.domain.user import User
from app.services.tutor_service import TutorService
from app.dependencies import get_tutor_service

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response schemas
class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


@router.post(
    "/topics/{topic_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_200_OK
)
async def send_message(
    topic_id: UUID,
    request: ChatMessageRequest,
    current_user: User = Depends(get_current_user),
    tutor_service: TutorService = Depends(get_tutor_service),
):
    """
    Send a message to the AI tutor for a specific topic.
    
    The AI can autonomously access topic content and flashcards using Function Calling.
    """
    logger.info(f"[AI Tutor] Received message from user {current_user.id} for topic {topic_id}")
    logger.info(f"[AI Tutor] Message preview: {request.message[:100]}...")
    
    try:
        logger.info(f"[AI Tutor] Calling tutor_service.chat...")
        response_msg = await tutor_service.chat(
            user_id=current_user.id,
            topic_id=topic_id,
            message=request.message,
        )
        
        logger.info(f"[AI Tutor] Response received: {len(response_msg.content)} chars")
        
        return ChatMessageResponse(
            id=str(response_msg.id),
            role=response_msg.role,
            content=response_msg.content,
            created_at=response_msg.created_at.isoformat(),
        )
    except Exception as e:
        logger.error(f"[AI Tutor] ERROR processing message: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get(
    "/topics/{topic_id}/messages",
    response_model=List[ChatMessageResponse],
    status_code=status.HTTP_200_OK
)
async def get_messages(
    topic_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    tutor_service: TutorService = Depends(get_tutor_service),
):
    """Get chat history for a topic"""
    logger.info(f"[AI Tutor] Getting history for topic {topic_id}, limit={limit}")
    
    try:
        messages = await tutor_service.get_history(topic_id, limit)
        logger.info(f"[AI Tutor] Retrieved {len(messages)} messages")
        
        return [
            ChatMessageResponse(
                id=str(msg.id),
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"[AI Tutor] ERROR retrieving messages: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve messages: {str(e)}"
        )


@router.delete(
    "/topics/{topic_id}/messages",
    status_code=status.HTTP_204_NO_CONTENT
)
async def clear_messages(
    topic_id: UUID,
    current_user: User = Depends(get_current_user),
    tutor_service: TutorService = Depends(get_tutor_service),
):
    """Clear chat history for a topic"""
    logger.info(f"[AI Tutor] Clearing history for topic {topic_id}")
    
    try:
        deleted_count = await tutor_service.clear_history(topic_id)
        logger.info(f"[AI Tutor] Cleared {deleted_count} messages")
    except Exception as e:
        logger.error(f"[AI Tutor] ERROR clearing messages: {type(e).__name__}: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear messages: {str(e)}"
        )
