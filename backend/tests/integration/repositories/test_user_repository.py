# backend/tests/integration/repositories/test_user_repository.py
from datetime import datetime
from uuid import uuid4

import pytest

from app.domain.user import User
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestUserRepository:
    """Integration tests for UserRepository"""

    async def test_create_user(self, test_session):
        """Test creating a user in database"""
        # Arrange
        repo = UserRepository(test_session)
        user = User(
            id=uuid4(),
            email="test_create@example.com",
            full_name="Test Create",
            created_at=datetime.now(),
        )

        # Act
        created_user = await repo.create(user)
        await test_session.flush()  # Ensure ID is generated/propagated if needed

        # Assert
        assert created_user.id is not None
        assert created_user.email == "test_create@example.com"

        # Verify persistence
        # We need to clear session or query directly to ensure it's in DB
        # But here we are in same transaction, so it should be visible
        retrieved = await repo.get_by_email("test_create@example.com")
        assert retrieved is not None
        assert retrieved.id == created_user.id

    async def test_update_user(self, test_session):
        """Test updating user"""
        # Arrange
        repo = UserRepository(test_session)
        user = User(
            id=uuid4(),
            email="update@test.com",
            full_name="Original Name",
            created_at=datetime.now(),
        )
        created = await repo.create(user)
        await test_session.flush()

        # Act
        created.full_name = "Updated Name"
        created.subscription_plan = "pro"
        await repo.update(created)
        await test_session.flush()

        # Assert
        retrieved = await repo.get_by_id(created.id)
        assert retrieved.full_name == "Updated Name"
        assert retrieved.subscription_plan == "pro"

    async def test_get_by_email(self, test_session):
        """Test get by email"""
        repo = UserRepository(test_session)
        user = User(
            id=uuid4(),
            email="findme@test.com",
            full_name="Find Me",
            created_at=datetime.now(),
        )
        await repo.create(user)
        await test_session.flush()

        found = await repo.get_by_email("findme@test.com")
        assert found is not None
        assert found.id == user.id

        not_found = await repo.get_by_email("missing@test.com")
        assert not_found is None

    async def test_exists_by_email(self, test_session):
        """Test exists by email"""
        repo = UserRepository(test_session)
        user = User(
            id=uuid4(),
            email="exists@test.com",
            full_name="Exists",
            created_at=datetime.now(),
        )
        await repo.create(user)
        await test_session.flush()

        assert await repo.exists_by_email("exists@test.com") is True
        assert await repo.exists_by_email("nope@test.com") is False
