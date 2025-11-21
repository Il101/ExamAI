"""
Tests for rate limiting functionality.
"""
import pytest
from unittest.mock import Mock
from app.core.rate_limit import get_user_rate_limit, dynamic_rate_limit
from app.domain.user import User


def test_get_user_rate_limit_free_tier():
    """Test rate limit for free tier users"""
    user = Mock(spec=User)
    user.subscription_tier = "free"
    
    limit = get_user_rate_limit(user)
    assert limit == "100/hour"


def test_get_user_rate_limit_pro_tier():
    """Test rate limit for pro tier users"""
    user = Mock(spec=User)
    user.subscription_tier = "pro"
    
    limit = get_user_rate_limit(user)
    assert limit == "1000/hour"


def test_get_user_rate_limit_premium_tier():
    """Test rate limit for premium tier users"""
    user = Mock(spec=User)
    user.subscription_tier = "premium"
    
    limit = get_user_rate_limit(user)
    assert limit == "10000/hour"


def test_get_user_rate_limit_no_user():
    """Test rate limit when no user is provided"""
    limit = get_user_rate_limit(None)
    assert limit == "100/hour"


def test_get_user_rate_limit_unknown_tier():
    """Test rate limit for unknown tier defaults to free"""
    user = Mock(spec=User)
    user.subscription_tier = "unknown"
    
    limit = get_user_rate_limit(user)
    assert limit == "100/hour"


def test_dynamic_rate_limit():
    """Test dynamic rate limit function"""
    # Mock request with user
    request = Mock()
    request.state.user = Mock(spec=User)
    request.state.user.subscription_tier = "pro"
    
    limit = dynamic_rate_limit(request)
    
    assert limit == "1000/hour"


def test_dynamic_rate_limit_no_user():
    """Test dynamic rate limit when no user in request"""
    # Mock request without user
    request = Mock()
    request.state.user = None
    
    limit = dynamic_rate_limit(request)
    
    assert limit == "100/hour"
