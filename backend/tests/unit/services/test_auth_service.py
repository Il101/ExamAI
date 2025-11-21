import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID, uuid4
from datetime import datetime

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
        email = "test@example.com"
        password = "SecurePass123!"
        full_name = "Test User"
        user_id = str(uuid4())

        # Mock Supabase response
        mock_user_resp = Mock()
        mock_user_resp.id = user_id
        mock_response = Mock()
        mock_response.user = mock_user_resp
        mock_supabase.auth.sign_up.return_value = mock_response

        # Mock Repo response
        mock_user_repo.create.return_value = User(
            id=UUID(user_id),
            email=email,
            full_name=full_name,
            created_at=datetime.now(),
        )

        user = await auth_service.register(email, password, full_name)

        assert user.email == email
        assert str(user.id) == user_id
        mock_supabase.auth.sign_up.assert_called_once()
        mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_supabase_failure(self, auth_service, mock_supabase):
        """Test registration when Supabase fails"""
        mock_supabase.auth.sign_up.side_effect = Exception("Supabase Error")

        with pytest.raises(ValueError, match="Registration failed: Supabase Error"):
            await auth_service.register("test@test.com", "pass", "Name")

    @pytest.mark.asyncio
    async def test_register_no_user_returned(self, auth_service, mock_supabase):
        """Test registration when Supabase returns no user"""
        mock_response = Mock()
        mock_response.user = None
        mock_supabase.auth.sign_up.return_value = mock_response

        with pytest.raises(ValueError, match="Registration failed: No user returned"):
            await auth_service.register("test@test.com", "pass", "Name")

    @pytest.mark.asyncio
    async def test_authenticate_success(self, auth_service, mock_supabase):
        """Test successful login"""
        mock_session = Mock()
        mock_session.access_token = "access"
        mock_session.refresh_token = "refresh"

        mock_response = Mock()
        mock_response.session = mock_session
        mock_response.user = Mock()

        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        result = await auth_service.authenticate("test@test.com", "pass")

        assert result["access_token"] == "access"
        assert result["refresh_token"] == "refresh"

    @pytest.mark.asyncio
    async def test_authenticate_failure(self, auth_service, mock_supabase):
        """Test login failure"""
        mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login")

        result = await auth_service.authenticate("test@test.com", "wrong")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_no_session(self, auth_service, mock_supabase):
        """Test login when no session returned"""
        mock_response = Mock()
        mock_response.session = None
        mock_supabase.auth.sign_in_with_password.return_value = mock_response

        result = await auth_service.authenticate("test@test.com", "pass")
        assert result is None

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_supabase):
        """Test token refresh success"""
        mock_session = Mock()
        mock_session.access_token = "new_access"
        mock_session.refresh_token = "new_refresh"

        mock_response = Mock()
        mock_response.session = mock_session
        mock_supabase.auth.refresh_session.return_value = mock_response

        result = await auth_service.refresh_token("old_refresh")

        assert result["access_token"] == "new_access"
        assert result["refresh_token"] == "new_refresh"

    @pytest.mark.asyncio
    async def test_refresh_token_failure(self, auth_service, mock_supabase):
        """Test token refresh failure"""
        mock_supabase.auth.refresh_session.side_effect = Exception("Failed")

        result = await auth_service.refresh_token("bad_refresh")
        assert result is None

    def test_get_user_by_token_success(self, auth_service, mock_supabase):
        """Test getting user by token success"""
        user_id = uuid4()
        mock_user_data = Mock()
        mock_user_data.id = str(user_id)
        mock_user_data.email = "test@test.com"
        mock_user_data.user_metadata = {"full_name": "Test User"}
        mock_user_data.email_confirmed_at = "2023-01-01"

        mock_response = Mock()
        mock_response.user = mock_user_data
        mock_supabase.auth.get_user.return_value = mock_response

        user = auth_service.get_user_by_token("token")

        assert user.id == user_id
        assert user.email == "test@test.com"
        assert user.full_name == "Test User"
        assert user.is_verified is True

    def test_get_user_by_token_failure(self, auth_service, mock_supabase):
        """Test getting user by token failure"""
        mock_supabase.auth.get_user.side_effect = Exception("Failed")
        user = auth_service.get_user_by_token("token")
        assert user is None

    def test_get_user_by_token_no_user(self, auth_service, mock_supabase):
        """Test getting user by token when no user returned"""
        mock_response = Mock()
        mock_response.user = None
        mock_supabase.auth.get_user.return_value = mock_response
        user = auth_service.get_user_by_token("token")
        assert user is None

    def test_verify_token_success(self, auth_service):
        """Test token verification"""
        user_id = str(uuid4())
        token = "valid.token.here"

        with patch("jose.jwt.decode") as mock_decode:
            mock_decode.return_value = {"sub": user_id}

            result = auth_service.verify_token(token)

            assert result == user_id
            mock_decode.assert_called_once()

    def test_verify_token_invalid(self, auth_service):
        """Test invalid token"""
        with patch("jose.jwt.decode") as mock_decode:
            from jose import JWTError
            mock_decode.side_effect = JWTError()

            result = auth_service.verify_token("invalid")
            assert result is None

    def test_verify_token_no_sub(self, auth_service):
        """Test token without sub"""
        with patch("jose.jwt.decode") as mock_decode:
            mock_decode.return_value = {}
            result = auth_service.verify_token("token")
            assert result is None

    @pytest.mark.asyncio
    async def test_update_profile_success(self, auth_service, mock_user_repo, mock_supabase):
        """Test profile update"""
        user_id = uuid4()
        full_name = "New Name"

        mock_user = User(id=user_id, email="test@test.com", full_name="Old Name")
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update.return_value = mock_user # returns updated object

        await auth_service.update_profile(user_id, full_name=full_name)

        mock_supabase.auth.update_user.assert_called_with({"data": {"full_name": full_name}})
        assert mock_user.full_name == full_name
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_supabase_failure(self, auth_service, mock_user_repo, mock_supabase):
        """Test profile update when supabase fails (should continue)"""
        user_id = uuid4()
        mock_user = User(id=user_id, email="test@test.com", full_name="Old Name")
        mock_user_repo.get_by_id.return_value = mock_user
        mock_user_repo.update.return_value = mock_user

        mock_supabase.auth.update_user.side_effect = Exception("Supabase fail")

        await auth_service.update_profile(user_id, full_name="New Name")

        assert mock_user.full_name == "New Name"
        mock_user_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_profile_user_not_found(self, auth_service, mock_user_repo):
        """Test profile update when user not found"""
        mock_user_repo.get_by_id.return_value = None
        with pytest.raises(ValueError, match="User not found"):
            await auth_service.update_profile(uuid4(), full_name="Test")

    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_supabase):
        """Test change password"""
        await auth_service.change_password("old", "new")
        mock_supabase.auth.update_user.assert_called_with({"password": "new"})

    @pytest.mark.asyncio
    async def test_change_password_failure(self, auth_service, mock_supabase):
        """Test change password failure"""
        mock_supabase.auth.update_user.side_effect = Exception("Fail")
        with pytest.raises(ValueError, match="Failed to change password"):
            await auth_service.change_password("old", "new")

    @pytest.mark.asyncio
    async def test_request_password_reset(self, auth_service, mock_supabase):
        """Test request password reset"""
        email = "test@test.com"
        await auth_service.request_password_reset(email)
        mock_supabase.auth.reset_password_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_failure(self, auth_service, mock_supabase):
        """Test request password reset failure (should be silent)"""
        mock_supabase.auth.reset_password_email.side_effect = Exception("Fail")
        await auth_service.request_password_reset("test@test.com")

    @pytest.mark.asyncio
    async def test_reset_password_with_token_success(self, auth_service, mock_supabase):
        """Test reset password with token"""
        token = "token"
        new_pass = "newpass"

        mock_response = Mock()
        mock_response.session = Mock()
        mock_supabase.auth.verify_otp.return_value = mock_response

        await auth_service.reset_password_with_token(token, new_pass)

        mock_supabase.auth.verify_otp.assert_called_once()
        mock_supabase.auth.update_user.assert_called_with({"password": new_pass})

    @pytest.mark.asyncio
    async def test_reset_password_with_token_invalid(self, auth_service, mock_supabase):
        """Test reset password with invalid token"""
        mock_response = Mock()
        mock_response.session = None
        mock_supabase.auth.verify_otp.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid or expired reset token"):
            await auth_service.reset_password_with_token("token", "pass")

    @pytest.mark.asyncio
    async def test_reset_password_with_token_exception(self, auth_service, mock_supabase):
        """Test reset password with exception"""
        mock_supabase.auth.verify_otp.side_effect = Exception("Fail")
        with pytest.raises(ValueError, match="Failed to reset password"):
            await auth_service.reset_password_with_token("token", "pass")
