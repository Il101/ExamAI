import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.dependencies import get_auth_service, get_db
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository

@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for auth endpoints"""

    @pytest.fixture
    def mock_supabase(self):
        mock = MagicMock()
        mock.auth = MagicMock()
        return mock

    @pytest.fixture
    async def client(self, test_session, mock_supabase):
        """Create async client with overrides"""
        
        # Create AuthService with mocked Supabase
        user_repo = UserRepository(test_session)
        
        with patch('app.services.auth_service.create_client', return_value=mock_supabase):
            auth_service = AuthService(user_repo)
            
        # Override dependency
        app.dependency_overrides[get_auth_service] = lambda: auth_service
        app.dependency_overrides[get_db] = lambda: test_session
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac
            
        # Clean up
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_success(self, client, mock_supabase):
        """Test successful registration"""
        # Arrange
        mock_user = MagicMock()
        mock_user.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_supabase.auth.sign_up.return_value.user = mock_user
        
        # Act
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "full_name": "New User"
            }
        )
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_login_success(self, client, mock_supabase):
        """Test successful login"""
        # Arrange
        mock_session = MagicMock()
        mock_session.access_token = "access_token_123"
        mock_session.refresh_token = "refresh_token_123"
        mock_session.user = MagicMock()
        
        mock_response = MagicMock()
        mock_response.session = mock_session
        
        mock_supabase.auth.sign_in_with_password.return_value = mock_response
        
        # Act
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@test.com",
                "password": "Password123!"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "access_token_123"
        assert data["refresh_token"] == "refresh_token_123"
