from typing import List, Dict, Any
from uuid import UUID

from app.domain.chat import ChatMessage
from app.domain.topic import Topic
from app.integrations.llm.gemini import GeminiProvider
from app.repositories.chat_repository import ChatMessageRepository
from app.repositories.topic_repository import TopicRepository
from app.repositories.review_repository import ReviewItemRepository
from app.repositories.exam_repository import ExamRepository
from app.utils.content_cleaner import strip_analysis_tags
from app.core.rate_limiter import tutor_usage_tracker
from app.services.subscription_service import SubscriptionService


class TutorService:
    """
    AI Tutor service with Function Calling support.
    Provides interactive chat with access to topic content and flashcards.
    """

    def __init__(
        self,
        llm: GeminiProvider,
        chat_repo: ChatMessageRepository,
        topic_repo: TopicRepository,
        review_repo: ReviewItemRepository,
        exam_repo: ExamRepository,
        subscription_service: SubscriptionService,
    ):
        self.llm = llm
        self.chat_repo = chat_repo
        self.topic_repo = topic_repo
        self.review_repo = review_repo
        self.exam_repo = exam_repo
        self.subscription_service = subscription_service

    def _get_tool_declarations(self) -> List[Dict[str, Any]]:
        """Define tools available to the AI"""
        return [
            {
                "function_declarations": [
                    {
                        "name": "get_topic_content",
                        "description": "Get the full lecture notes/content for a specific topic",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "topic_id": {
                                    "type": "string",
                                    "description": "UUID of the topic"
                                }
                            },
                            "required": ["topic_id"]
                        }
                    },
                    {
                        "name": "get_flashcards",
                        "description": "Get flashcards (review items) for a specific topic",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "topic_id": {
                                    "type": "string",
                                    "description": "UUID of the topic"
                                },
                                "limit": {
                                    "type": "integer",
                                    "description": "Maximum number of flashcards to return",
                                    "default": 5
                                }
                            },
                            "required": ["topic_id"]
                        }
                    }
                ]
            }
        ]

    async def _get_topic_content(self, topic_id: str) -> str:
        """Tool function: Get topic content"""
        try:
            topic = await self.topic_repo.get_by_id(UUID(topic_id))
            if not topic:
                return "Topic not found"
            return topic.content or "No content available for this topic"
        except Exception as e:
            return f"Error retrieving topic: {str(e)}"

    async def _get_flashcards(self, topic_id: str, limit: int = 5) -> str:
        """Tool function: Get flashcards for topic"""
        try:
            cards = await self.review_repo.list_by_topic(UUID(topic_id))
            if not cards:
                return "No flashcards available for this topic"
            
            # Format flashcards as text
            result = []
            for i, card in enumerate(cards[:limit], 1):
                result.append(f"{i}. Q: {card.question}\n   A: {card.answer}")
            
            return "\n\n".join(result)
        except Exception as e:
            return f"Error retrieving flashcards: {str(e)}"

    async def _get_current_topic_content(self, topic_id: UUID) -> str:
        """Get content for the current topic (for grounding)"""
        try:
            topic = await self.topic_repo.get_by_id(topic_id)
            if not topic or not topic.content:
                return "No content available for this topic yet."
            return topic.content
        except Exception as e:
            return f"Error: {str(e)}"

    async def _get_course_outline(self, topic_id: UUID) -> str:
        """Get formatted course outline for tool calling context"""
        try:
            # Get current topic to find exam_id
            topic = await self.topic_repo.get_by_id(topic_id)
            if not topic:
                return "Course outline unavailable"
            
            # Get all topics in this exam
            all_topics = await self.topic_repo.get_by_exam_id(topic.exam_id)
            
            if not all_topics:
                return "No topics available"
            
            # Format as numbered list
            lines = []
            for idx, t in enumerate(sorted(all_topics, key=lambda x: x.order_index), start=1):
                lines.append(f'{idx}. {t.id}: "{t.topic_name}"')
            
            return '\n'.join(lines)
        except Exception as e:
            return f"Error: {str(e)}"

    async def chat(
        self,
        user_id: UUID,
        topic_id: UUID,
        message: str,
    ) -> ChatMessage:
        """
        Send a message to the AI tutor and get a response.
        
        Args:
            user_id: User ID
            topic_id: Topic ID (context for the chat)
            message: User's message
            
        Returns:
            AI's response as ChatMessage
        """
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[TutorService] Starting chat for user={user_id}, topic={topic_id}")

        # Check daily limits
        try:
            subscription = await self.subscription_service.get_user_subscription(user_id)
            limits = subscription.get_limits()
            daily_limit = limits.get("daily_tutor_messages")
            
            if daily_limit is not None:
                current_usage = await tutor_usage_tracker.get_count(str(user_id))
                if current_usage >= daily_limit:
                    logger.warning(f"[TutorService] User {user_id} reached daily limit: {current_usage}/{daily_limit}")
                    raise ValueError(f"Daily tutor message limit reached ({daily_limit}). Upgrade for more!")
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"[TutorService] Error checking limits (failing open): {e}")
        
        # Save user message
        try:
            user_msg = ChatMessage(
                user_id=user_id,
                topic_id=topic_id,
                role="user",
                content=message,
            )
            await self.chat_repo.create(user_msg)
            logger.info(f"[TutorService] User message saved to DB")
        except Exception as e:
            logger.error(f"[TutorService] Failed to save user message: {e}")
            raise

        # Get chat history for context
        try:
            history = await self.chat_repo.list_by_topic(topic_id, limit=10)
            logger.info(f"[TutorService] Retrieved {len(history)} messages from history")
        except Exception as e:
            logger.error(f"[TutorService] Failed to get history: {e}")
            raise
        
        # Build conversation context
        context_messages = []
        for msg in history[-5:]:  # Last 5 messages
            context_messages.append(f"{msg.role}: {msg.content}")
        
        context = "\n".join(context_messages) if context_messages else ""
        logger.info(f"[TutorService] Built context with {len(context_messages)} messages")
        
        # Get current topic content for grounding
        try:
            current_study_notes = await self._get_current_topic_content(topic_id)
            logger.info(f"[TutorService] Retrieved topic content: {len(current_study_notes)} chars")
        except Exception as e:
            logger.error(f"[TutorService] Failed to get topic content: {e}")
            current_study_notes = "Content unavailable"
        
        # Get course outline for tool context
        try:
            course_outline = await self._get_course_outline(topic_id)
            logger.info(f"[TutorService] Retrieved course outline: {len(course_outline)} chars")
        except Exception as e:
            logger.error(f"[TutorService] Failed to get course outline: {e}")
            course_outline = "Outline unavailable"
        
        # Load prompt template with grounding
        from app.prompts import load_prompt
        
        try:
            prompt = load_prompt(
                'tutor/chat_system.txt',
                context=context,
                message=message,
                current_study_notes=current_study_notes,
                course_outline=course_outline
            )
            logger.info(f"[TutorService] Loaded prompt template: {len(prompt)} chars")
        except Exception as e:
            logger.error(f"[TutorService] Failed to load prompt: {e}")
            raise


        # Define tool functions mapping
        # Note: We pass the actual async methods, not lambdas
        tool_functions = {
            "get_topic_content": self._get_topic_content,
            "get_flashcards": self._get_flashcards,
        }

        # Call LLM with tools
        try:
            logger.info(f"[TutorService] Calling LLM with tools...")
            response = await self.llm.generate_with_tools(
                prompt=prompt,
                tools=self._get_tool_declarations(),
                tool_functions=tool_functions,
                temperature=0.7,
                system_prompt="You are a helpful AI tutor.",
            )
            logger.info(f"[TutorService] LLM response received: {len(response.content)} chars")
        except Exception as e:
            logger.error(f"[TutorService] LLM generation failed: {type(e).__name__}: {str(e)}")
            logger.exception("Full LLM error traceback:")
            raise
        
        # Clean response (remove <analysis> tags)
        cleaned_response = strip_analysis_tags(response.content)
        logger.info(f"[TutorService] Response cleaned: {len(cleaned_response)} chars")

        # Increment usage counter after successful response
        try:
            await tutor_usage_tracker.increment(str(user_id))
        except Exception as e:
            logger.error(f"[TutorService] Failed to increment usage counter: {e}")

        # Save assistant response
        try:
            assistant_msg = ChatMessage(
                user_id=user_id,
                topic_id=topic_id,
                role="assistant",
                content=cleaned_response,
            )
            await self.chat_repo.create(assistant_msg)
            logger.info(f"[TutorService] Assistant message saved to DB, id={assistant_msg.id}")
        except Exception as e:
            logger.error(f"[TutorService] Failed to save assistant message: {e}")
            raise

        return assistant_msg

    async def get_history(self, topic_id: UUID, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a topic"""
        return await self.chat_repo.list_by_topic(topic_id, limit)

    async def clear_history(self, topic_id: UUID) -> int:
        """Clear chat history for a topic"""
        return await self.chat_repo.delete_by_topic(topic_id)
