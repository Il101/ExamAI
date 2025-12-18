"""
Simple API metrics tracker for Gemini

Tracks basic metrics without over-engineering.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
import logging
import uuid
from datetime import datetime, timezone

from app.db.session import AsyncSessionLocal
from app.db.models.llm_usage import LLMUsageLogModel

logger = logging.getLogger(__name__)


async def record_usage_to_db(
    model_name: str,
    provider: str,
    operation_type: str,
    input_tokens: int,
    output_tokens: int,
    cost_usd: float,
    duration_ms: Optional[float] = None,
    cache_hit: bool = False,
    user_id: Optional[uuid.UUID] = None,
    study_material_id: Optional[uuid.UUID] = None,
    request_metadata: Optional[Dict[str, Any]] = None,
    error_occurred: bool = False,
    error_message: Optional[str] = None,
):
    """
    Persist LLM usage metrics to the database in the background.
    
    This function should be called using asyncio.create_task() to avoid
    blocking the main execution flow.
    """
    try:
        async with AsyncSessionLocal() as session:
            log_entry = LLMUsageLogModel(
                user_id=user_id,
                study_material_id=study_material_id,
                model_name=model_name,
                provider=provider,
                operation_type=operation_type,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                response_time_ms=int(duration_ms) if duration_ms is not None else None,
                cache_hit=cache_hit,
                request_metadata=request_metadata or {},
                error_occurred=error_occurred,
                error_message=error_message,
                created_at=datetime.now(timezone.utc)
            )
            session.add(log_entry)
            await session.commit()
            
    except Exception as e:
        # We log and ignore database errors to prevent LLM logging from 
        # crashing the main application or services.
        logger.error(f"Failed to record LLM usage to DB: {str(e)}", exc_info=True)


@dataclass
class APIMetrics:
    """Simple metrics for API calls"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    
    def record_success(self, tokens_in: int, tokens_out: int, cost: float, duration_ms: float):
        """Record successful API call"""
        self.total_calls += 1
        self.successful_calls += 1
        self.total_tokens_input += tokens_in
        self.total_tokens_output += tokens_out
        self.total_cost_usd += cost
        self.total_duration_ms += duration_ms
    
    def record_failure(self, is_timeout: bool = False):
        """Record failed API call"""
        self.total_calls += 1
        self.failed_calls += 1
        if is_timeout:
            self.timeout_calls += 1
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if self.total_calls == 0:
            return "No API calls yet"
        
        success_rate = (self.successful_calls / self.total_calls) * 100
        avg_duration = self.total_duration_ms / self.successful_calls if self.successful_calls > 0 else 0
        
        return (
            f"API Metrics: {self.total_calls} calls, "
            f"{success_rate:.1f}% success, "
            f"{self.timeout_calls} timeouts, "
            f"{self.total_tokens_input + self.total_tokens_output:,} tokens, "
            f"${self.total_cost_usd:.4f} cost, "
            f"{avg_duration:.0f}ms avg"
        )


# Global metrics instance
_metrics = APIMetrics()


def get_metrics() -> APIMetrics:
    """Get global metrics instance"""
    return _metrics


def log_metrics_summary():
    """Log current metrics summary"""
    logger.info(f"[Gemini Metrics] {_metrics.get_summary()}")
