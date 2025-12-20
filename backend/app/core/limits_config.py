# backend/app/core/limits_config.py
"""
Centralized configuration for subscription limits.
This file is the single source of truth for all plan-based restrictions.
"""

from typing import Dict, Any, Optional

# Plan definitions with all limits
PLAN_LIMITS: Dict[str, Dict[str, Any]] = {
    "free": {
        "max_exams": 2,
        "max_topics_per_exam": 8,
        "daily_tutor_messages": 15,
        "max_simultaneous_sessions": 1,
        "daily_exam_creations": 2,
        "max_team_members": 1,
    },
    "pro": {
        "max_exams": 10,
        "max_topics_per_exam": 20,
        "daily_tutor_messages": 100,
        "max_simultaneous_sessions": 1,
        "daily_exam_creations": 3,
        "max_team_members": 1,
    },
    "premium": {
        "max_exams": None,  # Unlimited
        "max_topics_per_exam": None,  # Unlimited
        "daily_tutor_messages": None,  # Unlimited
        "max_simultaneous_sessions": 2,
        "daily_exam_creations": None,  # Unlimited
        "max_team_members": 1,
    },
    "team": {
        "max_exams": None,  # Unlimited
        "max_topics_per_exam": None,  # Unlimited
        "daily_tutor_messages": None,  # Unlimited
        "max_simultaneous_sessions": 5,
        "daily_exam_creations": None,  # Unlimited
        "max_team_members": 5,
    },
}

# Pricing in EUR
PLAN_PRICING: Dict[str, Dict[str, Any]] = {
    "free": {
        "monthly": 0,
        "yearly": 0,
    },
    "pro": {
        "monthly": 7.99,
        "yearly": 59.88,  # €4.99/mo (billed annually)
    },
    "premium": {
        "monthly": 14.99,
        "yearly": 119.88,  # €9.99/mo (billed annually)
    },
    "team": {
        "monthly": 39.99,
        "yearly": 299.88,  # €24.99/mo (billed annually)
    },
}


def get_limit(plan_type: str, limit_name: str) -> Optional[int]:
    """
    Get a specific limit for a plan.
    Returns None if unlimited.
    """
    plan = PLAN_LIMITS.get(plan_type, PLAN_LIMITS["free"])
    return plan.get(limit_name)


def is_within_limit(plan_type: str, limit_name: str, current_value: int) -> bool:
    """
    Check if a value is within the plan's limit.
    Returns True if unlimited or within limit.
    """
    limit = get_limit(plan_type, limit_name)
    if limit is None:
        return True  # Unlimited
    return current_value < limit


def get_all_limits(plan_type: str) -> Dict[str, Any]:
    """Get all limits for a plan."""
    return PLAN_LIMITS.get(plan_type, PLAN_LIMITS["free"])
