import pytest
from uuid import uuid4
from datetime import datetime

from app.repositories.user_repository import UserRepository
from app.domain.user import User

@pytest.mark.integration
class TestUserRepository:
    """Integration tests for UserRepository"""

    @pytest.mark.asyncio
    async def test_create_user(self, test_session):
        """Test creating a user in database"""
        # Arrange
        repo = UserRepository(test_session)
        user = User(
            id=uuid4(),
            email="test@example.com",
            full_name="Test User",
            created_at=datetime.now()
        )
        
        # Act
        created_user = await repo.create(user)
        await test_session.commit()
        
        # Assert
        assert created_user.id is not None
        assert created_user.email == "test@example.com"
        
        # Verify persistence
        retrieved = await repo.get_by_email("test@example.com")
        assert retrieved is not None
        assert retrieved.id == created_user.id

    @pytest.mark.asyncio
    async def test_update_user(self, test_session):
        """Test updating user"""
        # Arrange
        repo = UserRepository(test_session)
        user = User(
            id=uuid4(),
            email="update@test.com",
            full_name="Original Name",
            created_at=datetime.now()
        )
        created = await repo.create(user)
        await test_session.commit()
        
        # Act
        created.full_name = "Updated Name"
        created.subscription_plan = "pro"
        updated = await repo.update(created)
        await test_session.commit()
        
        # Assert
        retrieved = await repo.get_by_id(created.id)
        assert retrieved.full_name == "Updated Name"
        assert retrieved.subscription_plan == "pro"
