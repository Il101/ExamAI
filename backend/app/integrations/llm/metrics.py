"""
Simple API metrics tracker for Gemini

Tracks basic metrics without over-engineering.
"""

import time
from dataclasses import dataclass, field
from typing import Dict
import logging

logger = logging.getLogger(__name__)


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
