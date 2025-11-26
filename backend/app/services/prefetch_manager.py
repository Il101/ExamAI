"""Redis-based prefetch state manager"""
import json
from redis import Redis
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PrefetchManager:
    """Manages prefetch state across multiple server instances using Redis"""
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    def set_generating(self, exam_id: UUID, topic_id: str) -> None:
        """
        Mark topic as being generated
        
        Args:
            exam_id: Exam UUID
            topic_id: Topic identifier (e.g., "topic_01")
        """
        key = f"prefetch:{exam_id}:{topic_id}"
        data = {
            "status": "generating",
            "started_at": datetime.now().isoformat()
        }
        self.redis.setex(key, 3600, json.dumps(data))
        logger.debug(f"Marked {topic_id} as generating for exam {exam_id}")
    
    def set_completed(self, exam_id: UUID, topic_id: str, content: str) -> None:
        """
        Mark topic as completed with generated content
        
        Args:
            exam_id: Exam UUID
            topic_id: Topic identifier
            content: Generated content (markdown)
        """
        key = f"prefetch:{exam_id}:{topic_id}"
        data = {
            "status": "completed",
            "content": content,
            "completed_at": datetime.now().isoformat()
        }
        # Store for 1 hour
        self.redis.setex(key, 3600, json.dumps(data))
        logger.info(f"Marked {topic_id} as completed for exam {exam_id}")
    
    def set_failed(self, exam_id: UUID, topic_id: str, error: str) -> None:
        """
        Mark topic generation as failed
        
        Args:
            exam_id: Exam UUID
            topic_id: Topic identifier
            error: Error message
        """
        key = f"prefetch:{exam_id}:{topic_id}"
        data = {
            "status": "failed",
            "error": error,
            "failed_at": datetime.now().isoformat()
        }
        self.redis.setex(key, 3600, json.dumps(data))
        logger.error(f"Marked {topic_id} as failed for exam {exam_id}: {error}")
    
    def get_status(self, exam_id: UUID, topic_id: str) -> Optional[Dict]:
        """
        Get topic generation status
        
        Args:
            exam_id: Exam UUID
            topic_id: Topic identifier
        
        Returns:
            Status dict or None if not found
        """
        key = f"prefetch:{exam_id}:{topic_id}"
        data = self.redis.get(key)
        
        if data:
            return json.loads(data)
        return None
    
    def get_content(self, exam_id: UUID, topic_id: str) -> Optional[str]:
        """
        Get generated content if available
        
        Args:
            exam_id: Exam UUID
            topic_id: Topic identifier
        
        Returns:
            Generated content or None
        """
        status = self.get_status(exam_id, topic_id)
        if status and status.get("status") == "completed":
            return status.get("content")
        return None
    
    def clear_exam(self, exam_id: UUID) -> int:
        """
        Clear all prefetch data for an exam
        
        Args:
            exam_id: Exam UUID
        
        Returns:
            Number of keys deleted
        """
        pattern = f"prefetch:{exam_id}:*"
        keys = self.redis.keys(pattern)
        if keys:
            deleted = self.redis.delete(*keys)
            logger.info(f"Cleared {deleted} prefetch keys for exam {exam_id}")
            return deleted
        return 0
