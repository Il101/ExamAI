import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.auth_service import AuthService
from app.domain.user import User
from app.core.exceptions import AuthenticationException


@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def mock_supabase():
    mock_client = MagicMock()
    mock_client.auth = MagicMock()
    return mock_client

@pytest.fixture
def auth_service(mock_user_repo, mock_supabase):
    with patch('app.services.auth_service.create_client', return_value=mock_supabase):
        service = AuthService(user_repo=mock_user_repo)
        yield service

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
        mock_auth_response = MagicMock()
        mock_auth_response.user.id = user_id
        mock_supabase.auth.sign_up.return_value = mock_auth_response

        # Mock Repo response
        mock_user_repo.create.return_value = User(
            id=user_id,
            email=email,
            full_name=full_name,
            created_at=datetime.now()
        )
        
        # Act
        user = await auth_service.register(
            email=email,
            password=password,
            full_name=full_name
        )
        
        # Assert
        assert user.email == email
        mock_supabase.auth.sign_up.assert_called_once_with({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name
                }
            }
        })
        mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_supabase_failure(self, auth_service, mock_user_repo, mock_supabase):
        """Test registration when Supabase fails"""
        # Arrange
        mock_supabase.auth.sign_up.side_effect = Exception("Supabase error")
        
        # Act & Assert
        with pytest.raises(ValueError, match="Registration failed: Supabase error"):
            await auth_service.register(
                email="test@example.com",
                password="password",
                full_name="Test"
            )

    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_service, mock_supabase):
        """Test successful authentication"""
        # Arrange
        email = "test@example.com"
        password = "correct_password"
        
        mock_session = MagicMock()
        mock_session.access_token = "token"
        mock_session.refresh_token = "refresh"
        
        mock_response = MagicMock()
        mock_response.session = mock_session
        mock_response.user = MagicMock()
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        # Act
        result = await auth_service.authenticate(email, password)
        
        # Assert
        assert result is not None
        assert result["access_token"] == "token"
        mock_supabase.auth.sign_in_with_password.assert_called_once_with({
            "email": email,
            "password": password
        })

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, auth_service, mock_supabase):
        """Test authentication failure"""
        # Arrange
        mock_response = MagicMock()
        mock_response.session = None
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        # Act
        result = await auth_service.authenticate("test@example.com", "wrong")
        
        # Assert
        assert result is None
