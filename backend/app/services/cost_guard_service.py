from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.domain.user import User
from app.db.models.llm_usage import LLMUsageLogModel


class CostGuardService:
    """
    Service for tracking and limiting LLM usage costs with safety buffer.
    Prevents budget overruns from token estimation errors.
    
    CRITICAL: Uses 95% safety buffer to handle inaccurate token estimates.
    """
    
    # Daily limits by subscription plan (USD)
    DAILY_LIMITS = {
        "free": 0.50,      # $0.50/day
        "pro": 5.00,       # $5/day
        "premium": 20.00,  # $20/day
    }
    
    # Safety buffer: only allow operations up to 95% of remaining budget
    SAFETY_BUFFER_PERCENTAGE = 0.95
    
    # Overage handling policy
    OVERAGE_POLICY = {
        "free": {"max_overage_percent": 0, "action": "block"},
        "pro": {"max_overage_percent": 5, "action": "warn"},
        "premium": {"max_overage_percent": 10, "action": "allow"}
    }
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_budget(
        self,
        user: User,
        estimated_cost: float,
        apply_buffer: bool = True
    ) -> Dict[str, Any]:
        """
        Check if user has budget for request with safety buffer.
        
        Args:
            user: User entity
            estimated_cost: Estimated cost in USD
            apply_buffer: Whether to apply 95% safety buffer (default: True)
        
        Returns:
            {
                "allowed": bool,
                "remaining_budget": float,
                "usable_budget": float,
                "estimated_cost": float,
                "buffer_applied": bool,
                "reason": str  # If not allowed
            }
        """
        # Get daily limit
        daily_limit = self.DAILY_LIMITS.get(user.subscription_plan, self.DAILY_LIMITS["free"])
        
        # Get today's spending
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.sum(LLMUsageLogModel.cost_usd)).where(
            LLMUsageLogModel.user_id == user.id,
            LLMUsageLogModel.created_at >= today_start
        )
        
        result = await self.session.execute(stmt)
        today_spending = result.scalar_one_or_none() or 0.0
        
        remaining = daily_limit - today_spending
        
        # Apply safety buffer (95% of remaining)
        if apply_buffer:
            usable_budget = remaining * self.SAFETY_BUFFER_PERCENTAGE
        else:
            usable_budget = remaining
        
        # Check if within usable budget
        if estimated_cost <= usable_budget:
            return {
                "allowed": True,
                "remaining_budget": remaining,
                "usable_budget": usable_budget,
                "estimated_cost": estimated_cost,
                "buffer_applied": apply_buffer,
                "reason": None
            }
        else:
            # Calculate overage
            overage = estimated_cost - remaining
            overage_percentage = (overage / remaining * 100) if remaining > 0 else float('inf')
            
            return {
                "allowed": False,
                "remaining_budget": remaining,
                "usable_budget": usable_budget,
                "estimated_cost": estimated_cost,
                "overage_amount": overage,
                "overage_percentage": overage_percentage,
                "buffer_applied": apply_buffer,
                "reason": f"Insufficient budget. Need ${estimated_cost:.4f}, have ${usable_budget:.4f} available (95% safety buffer applied)"
            }

    async def handle_actual_cost_overage(
        self,
        user: User,
        estimated_cost: float,
        actual_cost: float
    ) -> Dict[str, Any]:
        """
        Handle cases where actual cost exceeds estimate.
        
        Returns:
            {
                "action": "allow|warn|block",
                "overage": float,
                "message": str
            }
        """
        if actual_cost <= estimated_cost:
            return {"action": "allow", "overage": 0, "message": "Within estimate"}
        
        overage = actual_cost - estimated_cost
        overage_percentage = (overage / estimated_cost * 100) if estimated_cost > 0 else float('inf')
        
        policy = self.OVERAGE_POLICY.get(
            user.subscription_plan,
            self.OVERAGE_POLICY["free"]
        )
        
        if overage_percentage <= policy["max_overage_percent"]:
            return {
                "action": policy["action"],
                "overage": overage,
                "message": f"Cost overrun of {overage_percentage:.1f}% allowed for {user.subscription_plan} tier"
            }
        else:
            return {
                "action": "block",
                "overage": overage,
                "message": f"Cost overrun of {overage_percentage:.1f}% exceeds {policy['max_overage_percent']}% limit"
            }
    
    async def get_remaining_budget(self, user: User) -> float:
        """Get remaining budget for today (USD)"""
        daily_limit = self.DAILY_LIMITS.get(user.subscription_plan, self.DAILY_LIMITS["free"])
        
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        stmt = select(func.sum(LLMUsageLogModel.cost_usd)).where(
            LLMUsageLogModel.user_id == user.id,
            LLMUsageLogModel.created_at >= today_start
        )
        
        result = await self.session.execute(stmt)
        today_spending = result.scalar_one_or_none() or 0.0
        
        return max(0, daily_limit - today_spending)

    async def log_usage(
        self,
        user_id: UUID,
        model_name: str,
        provider: str,
        operation_type: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        response_time_ms: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> LLMUsageLogModel:
        """Log LLM usage to database"""
        
        log_entry = LLMUsageLogModel(
            user_id=user_id,
            model_name=model_name,
            provider=provider,
            operation_type=operation_type,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            response_time_ms=response_time_ms,
            error_occurred=bool(error_message),
            error_message=error_message
        )
        
        self.session.add(log_entry)
        await self.session.commit()
        await self.session.refresh(log_entry)
        
        return log_entry

    async def get_usage_stats(
        self,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get usage statistics for user.
        
        Returns:
            {
                "total_cost": 12.50,
                "total_tokens": 500000,
                "operations_count": 25,
                "avg_cost_per_operation": 0.50
            }
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(
            func.sum(LLMUsageLogModel.cost_usd).label("total_cost"),
            func.sum(LLMUsageLogModel.input_tokens + LLMUsageLogModel.output_tokens).label("total_tokens"),
            func.count(LLMUsageLogModel.id).label("operations_count")
        ).where(
            LLMUsageLogModel.user_id == user_id,
            LLMUsageLogModel.created_at >= start_date
        )
        
        result = await self.session.execute(stmt)
        row = result.one()
        
        total_cost = row.total_cost or 0.0
        operations_count = row.operations_count or 0
        
        return {
            "total_cost": total_cost,
            "total_tokens": row.total_tokens or 0,
            "operations_count": operations_count,
            "avg_cost_per_operation": total_cost / operations_count if operations_count > 0 else 0.0
        }
