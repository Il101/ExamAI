# backend/tests/unit/domain/test_user.py
import pytest
from datetime import datetime
from app.domain.user import User


class TestUser:
    """Unit tests for User domain entity"""
    
    def test_create_valid_user(self):
        """Test creating valid user"""
        user = User(
            email="test@example.com",
            full_name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.subscription_plan == "free"
        assert user.is_verified is False
    
    def test_invalid_email_raises_error(self):
        """Test that invalid email raises ValueError"""
        with pytest.raises(ValueError, match="Invalid email format"):
            User(email="invalid-email", full_name="Test User")
    
    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError"""
        with pytest.raises(ValueError, match="at least 2 characters"):
            User(email="test@example.com", full_name="")
    
    def test_get_daily_token_limit(self):
        """Test token limits by subscription plan"""
        user = User(email="test@example.com", full_name="Test")
        
        assert user.get_daily_token_limit() == 50_000
        
        user.subscription_plan = "pro"
        assert user.get_daily_token_limit() == 500_000
        
        user.subscription_plan = "premium"
        assert user.get_daily_token_limit() == 2_000_000
    
    def test_mark_as_verified(self):
        """Test user verification"""
        user = User(
            email="test@example.com",
            full_name="Test",
            verification_token="abc123"
        )
        
        user.mark_as_verified()
        
        assert user.is_verified is True
        assert user.verification_token is None
    
    def test_upgrade_subscription(self):
        """Test subscription upgrade"""
        user = User(email="test@example.com", full_name="Test")
        
        user.upgrade_subscription("pro")
        assert user.subscription_plan == "pro"
        
        user.upgrade_subscription("premium")
        assert user.subscription_plan == "premium"
    
    def test_cannot_downgrade_subscription(self):
        """Test that downgrade raises error"""
        user = User(
            email="test@example.com",
            full_name="Test",
            subscription_plan="pro"
        )
        
        with pytest.raises(ValueError, match="Cannot downgrade"):
            user.upgrade_subscription("free")
