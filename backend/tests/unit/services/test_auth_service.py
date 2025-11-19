# backend/tests/unit/services/test_auth_service.py
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4

import pytest

from app.core.config import settings
from app.domain.user import User
from app.services.auth_service import AuthService


@pytest.fixture
def mock_user_repo():
    return AsyncMock()


@pytest.fixture
def mock_supabase():
    with patch("app.services.auth_service.create_client") as mock_create:
        mock_client = Mock()
        mock_create.return_value = mock_client
        yield mock_client


@pytest.fixture
def auth_service(mock_user_repo, mock_supabase):
    return AuthService(user_repo=mock_user_repo)


class TestAuthService:
    """Unit tests for AuthService"""

    @pytest.mark.asyncio
    async def test_register_success(self, auth_service, mock_user_repo, mock_supabase):
        """Test successful user registration"""
        # Arrange
        email = "test@example.com"
        password = "SecurePass123!"
        full_name = "Test User"
        user_id = str(uuid4())

        # Mock Supabase response
        mock_user = Mock()
        mock_user.id = user_id
        mock_response = Mock()
        mock_response.user = mock_user
        mock_supabase.auth.sign_up.return_value = mock_response

        # Mock Repo response
        mock_user_repo.create.return_value = User(
            id=UUID(user_id),
            email=email,
            full_name=full_name,
            created_at=datetime.now(),
        )

        # Act
        user = await auth_service.register(email, password, full_name)

        # Assert
        assert user.email == email
        assert str(user.id) == user_id
        mock_supabase.auth.sign_up.assert_called_once()
        mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_supabase_failure(self, auth_service, mock_supabase):
        """Test registration when Supabase fails"""
        # Arrange
        mock_supabase.auth.sign_up.side_effect = Exception("Supabase Error")

        # Act & Assert
        with pytest.raises(ValueError, match="Registration failed: Supabase Error"):
            await auth_service.register("test@test.com", "pass", "Name")

    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_service, mock_supabase):
        """Test successful login"""
        # Arrange
        mock_session = Mock()
        mock_session.access_token = "access"
        mock_session.refresh_token = "refresh"

        mock_response = Mock()
        mock_response.session = mock_session
        mock_response.user = Mock()

        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        # Act
        result = await auth_service.authenticate("test@test.com", "pass")

        # Assert
        assert result["access_token"] == "access"
        assert result["refresh_token"] == "refresh"

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, auth_service, mock_supabase):
        """Test login failure"""
        # Arrange
        mock_supabase.auth.sign_in_with_password.side_effect = Exception(
            "Invalid login"
        )

        # Act
        result = await auth_service.authenticate("test@test.com", "wrong")

        # Assert
        assert result is None

    def test_verify_token_success(self, auth_service):
        """Test token verification"""
        # Arrange
        user_id = str(uuid4())
        token = "valid.token.here"

        with patch("jose.jwt.decode") as mock_decode:
            mock_decode.return_value = {"sub": user_id}

            # Act
            result = auth_service.verify_token(token)

            # Assert
            assert result == user_id
            mock_decode.assert_called_once()

    def test_verify_token_invalid(self, auth_service):
        """Test invalid token"""
        with patch("jose.jwt.decode") as mock_decode:
            from jose import JWTError

            mock_decode.side_effect = JWTError()

            # Act
            result = auth_service.verify_token("invalid")

            # Assert
            assert result is None
