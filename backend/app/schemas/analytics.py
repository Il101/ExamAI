from datetime import date
from typing import List
from pydantic import BaseModel


class DailyProgress(BaseModel):
    """Daily study progress"""

    date: date
    cards_reviewed: int
    cards_learned: int
    minutes_studied: int


class RetentionPoint(BaseModel):
    """Retention curve point"""

    days_since_review: int
    retention_rate: float  # 0.0 to 1.0


class HeatmapPoint(BaseModel):
    """Activity heatmap point"""

    date: date
    count: int
    level: int  # 0-4 intensity


class AnalyticsResponse(BaseModel):
    """Comprehensive analytics response"""

    daily_progress: List[DailyProgress]
    retention_curve: List[RetentionPoint]
    activity_heatmap: List[HeatmapPoint]

    # Summary stats
    total_cards_learned: int
    total_minutes_studied: int
    current_streak: int
    longest_streak: int
