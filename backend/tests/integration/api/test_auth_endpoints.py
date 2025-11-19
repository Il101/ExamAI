# backend/tests/integration/api/test_auth_endpoints.py
import pytest
from unittest.mock import AsyncMock


@pytest.mark.integration
class TestAuthEndpoints:
    """Integration tests for auth endpoints"""

    @pytest.mark.asyncio
    async def test_register_success(self, client, mock_auth_service):
        """Test successful registration"""
        # Arrange
        from datetime import datetime
        from uuid import UUID

        mock_auth_service.register.return_value = AsyncMock(
            id=UUID("12345678-1234-5678-1234-567812345678"),
            email="newuser@test.com",
            full_name="New User",
            is_verified=False,
            role="user",
            subscription_plan="free",
            created_at=datetime.utcnow(),
            last_login=None,
            preferred_language="en",
            timezone="UTC",
        )

        # Act
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "SecurePass123!",
                "full_name": "New User",
            },
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert "id" in data
        mock_auth_service.register.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_validation_error(self, client):
        """Test registration validation error (short password)"""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@test.com", "password": "short", "full_name": "Test"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_service_error(self, client, mock_auth_service):
        """Test registration service error"""
        # Arrange
        mock_auth_service.register.side_effect = ValueError("Email taken")

        # Act
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "taken@test.com",
                "password": "SecurePass123!",
                "full_name": "Test",
            },
        )

        # Assert
        assert response.status_code == 400
        assert "Email taken" in response.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_login_success(self, client, mock_auth_service):
        """Test successful login"""
        # Arrange
        mock_auth_service.authenticate.return_value = {
            "access_token": "valid_token",
            "refresh_token": "valid_refresh",
            "expires_in": 3600,
        }

        # Act
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@test.com", "password": "Password123!"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "valid_token"
        assert data["refresh_token"] == "valid_refresh"

    @pytest.mark.asyncio
    async def test_login_failure(self, client, mock_auth_service):
        """Test login failure"""
        # Arrange
        mock_auth_service.authenticate.return_value = None

        # Act
        response = await client.post(
            "/api/v1/auth/login", json={"email": "wrong@test.com", "password": "wrong"}
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["error"]["message"]

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client, mock_auth_service):
        """Test successful token refresh"""
        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "valid_refresh"}
        )

        assert response.status_code == 200
        assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_token_failure(self, client, mock_auth_service):
        """Test refresh token failure"""
        mock_auth_service.refresh_token.return_value = None

        response = await client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid"}
        )

        assert response.status_code == 401
