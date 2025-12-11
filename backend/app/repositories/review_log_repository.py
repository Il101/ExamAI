from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.review_log import ReviewLogModel
from app.domain.review_log import ReviewLog
from app.repositories.base import BaseRepository
from app.schemas.analytics import RetentionPoint

from app.db.mappers.review_log_mapper import ReviewLogMapper

class ReviewLogRepository(BaseRepository[ReviewLog, ReviewLogModel]):
    """Repository for ReviewLog entity"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ReviewLogModel, ReviewLogMapper)

    async def add_log(self, log: ReviewLog) -> ReviewLog:
        """Add a new review log entry"""
        model = ReviewLogMapper.to_model(log)
        self.session.add(model)
        await self.session.flush()  # Let get_db() handle commit
        await self.session.refresh(model)
        return ReviewLogMapper.to_domain(model)

    async def get_retention_stats(self, user_id: UUID) -> List[RetentionPoint]:
        """
        Calculate retention curve based on review history.
        Groups reviews by interval buckets and calculates pass rate.
        """
        # Buckets: 1, 3, 7, 14, 30 days
        # We want to find the average retention rate for reviews that happened around these intervals.
        
        # Query: Select interval_days, count(*), sum(case when rating > 1 then 1 else 0 end)
        # Group by interval_days
        
        stmt = (
            select(
                ReviewLogModel.interval_days,
                func.count().label("total"),
                func.sum(case((ReviewLogModel.rating > 1, 1), else_=0)).label("passed")
            )
            .where(ReviewLogModel.user_id == user_id)
            .group_by(ReviewLogModel.interval_days)
        )
        
        result = await self.session.execute(stmt)
        
        # Aggregate into buckets
        buckets = {1: [], 3: [], 7: [], 14: [], 30: []}
        
        for row in result:
            interval = row.interval_days
            total = row.total
            passed = row.passed or 0
            
            # Find closest bucket
            closest_bucket = min(buckets.keys(), key=lambda x: abs(x - interval))
            
            # Only include if it's reasonably close (e.g. within 20% or +/- 1 day)
            # For simplicity, we just map to closest for now
            buckets[closest_bucket].append((total, passed))
            
        retention_points = []
        for days in sorted(buckets.keys()):
            data = buckets[days]
            if not data:
                # Fallback to theoretical curve if no data
                # R = 0.9 ^ (days / stability_avg) - hard to guess stability
                # Just return a default decay
                retention = 0.9 ** days # Simple exponential decay proxy
            else:
                total_reviews = sum(d[0] for d in data)
                total_passed = sum(d[1] for d in data)
                retention = total_passed / total_reviews if total_reviews > 0 else 0.0
                
            retention_points.append(RetentionPoint(
                days_since_review=days,
                retention_rate=round(retention, 2)
            ))
            
        return retention_points
