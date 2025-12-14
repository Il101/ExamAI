from typing import Any, Dict, Optional
from uuid import UUID, uuid4
import logging

from jose import JWTError, jwt
from supabase import Client, create_client

from app.core.config import settings
from app.domain.user import User
from app.repositories.user_repository import UserRepository


class AuthService:
    """
    Authentication service using Supabase Auth.
    Handles registration, login, and token verification via Supabase.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.supabase: Client = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_KEY
        )
        self.logger = logging.getLogger(__name__)

    # Registration

    async def register(self, email: str, password: str, full_name: str) -> User:
        """
        Register new user via Supabase Auth.

        Args:
            email: User email
            password: Plain password
            full_name: User full name

        Returns:
            Created user

        Raises:
            ValueError: If validation fails or email exists
        """
        try:
            # 1. Register with Supabase Auth
            # Set email redirect URL to frontend for email verification
            redirect_url = f"{settings.FRONTEND_URL}/auth/callback"
            
            auth_response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {"full_name": full_name},
                        "email_redirect_to": redirect_url,
                    },
                }
            )

            if not auth_response.user:
                raise ValueError("Registration failed: No user returned from Supabase")

            user_id = UUID(auth_response.user.id)

            # 2. Create or update user profile in our DB (public.users)
            # Check if user already exists (e.g., from a previous registration attempt)
            existing_user = await self.user_repo.get_by_id(user_id)
            
            if existing_user:
                # User already exists, update their information
                existing_user.email = email.lower().strip()
                existing_user.full_name = full_name.strip()
                existing_user.is_verified = False
                updated_user = await self.user_repo.update(existing_user)
                return updated_user
            else:
                # Create new user profile
                user = User(
                    id=user_id,
                    email=email.lower().strip(),
                    full_name=full_name.strip(),
                    is_verified=False,  # Supabase handles verification
                )

                created = await self.user_repo.create(user)
                return created

        except Exception as e:
            error_msg = str(e).lower()

            # Логируем конкретную ошибку для расследования, но наружу даём контролируемое сообщение
            self.logger.warning("Registration failed", extra={"email": email, "error": error_msg})

            if "already" in error_msg and "email" in error_msg:
                raise ValueError("Email already registered. Try logging in or reset your password.")
            if "already registered" in error_msg or "user already" in error_msg:
                raise ValueError("Email already registered. Try logging in or reset your password.")

            raise ValueError("Registration failed. Please try again later.")

    # Login

    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user by email and password via Supabase.

        Returns:
            Dict with session info (access_token, refresh_token, user)
        """
        try:
            response = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if not response.session:
                return None

            # Sync user profile if needed (e.g. last login)
            # We can do this asynchronously or just rely on the token

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": response.user,
            }

        except Exception as e:
            self.logger.warning("Login failed", extra={"email": email, "error": str(e).lower()})
            return None

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh session using refresh token.
        """
        try:
            response = self.supabase.auth.refresh_session(refresh_token)

            if not response.session:
                return None

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": response.user,
            }
        except Exception as e:
            self.logger.warning("Refresh token failed", extra={"error": str(e).lower()})
            return None

    # Token Verification

    def get_user_by_token(self, token: str) -> Optional[User]:
        """
        Get user from Supabase using the token directly.
        This validates the token via Supabase API.
        """
        try:
            response = self.supabase.auth.get_user(token)
            if not response.user:
                return None

            user_data = response.user
            user_id = UUID(user_data.id)

            # Safe extraction of metadata
            meta = user_data.user_metadata or {}
            
            return User(
                id=user_id,
                email=user_data.email,
                full_name=meta.get("full_name", "") or user_data.email.split("@")[0], # Fallback to email prefix
                is_verified=user_data.email_confirmed_at is not None,
            )
        except Exception as e:
            print(f"Supabase Auth Error: {e}")
            return None

    def verify_token(self, token: str) -> Optional[str]:
        """
        Verify Supabase JWT token and extract user_id.

        Returns:
            user_id if valid, None otherwise
        """
        try:
            # Supabase JWTs are signed with the project's JWT Secret (HS256)
            # We use settings.SECRET_KEY which should be set to Supabase JWT Secret
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM],
                audience="authenticated",  # Supabase default audience
            )

            user_id: Optional[str] = payload.get("sub")

            if user_id is None:
                return None

            return user_id

        except JWTError:
            return None

    # Email verification

    async def verify_email(self, token: str) -> bool:
        """
        Verify user email.
        With Supabase, this is usually handled by the frontend or Supabase's email link.
        If we need to handle it backend-side, we'd use verify_otp.
        For now, we'll assume this is handled by Supabase.
        """

    # Profile Management

    async def update_profile(
        self,
        user_id: UUID,
        full_name: Optional[str] = None,
        daily_study_goal_minutes: Optional[int] = None,
        preferred_language: Optional[str] = None,
        timezone: Optional[str] = None,
    ) -> User:
        """
        Update user profile in DB and Supabase.
        """
        # 1. Update in Supabase if needed
        if full_name:
            try:
                self.supabase.auth.update_user({"data": {"full_name": full_name}})
            except Exception as e:
                # Log error but continue to update local DB
                print(f"Failed to update Supabase profile: {e}")

        # 2. Update in local DB
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")

        if full_name:
            user.full_name = full_name

        if daily_study_goal_minutes is not None:
            user.daily_study_goal_minutes = daily_study_goal_minutes

        if preferred_language:
            user.preferred_language = preferred_language

        if timezone:
            user.timezone = timezone

        updated_user = await self.user_repo.update(user)
        return updated_user

    async def change_password(self, email: str, current_password: str, new_password: str) -> None:
        """
        Change user password safely.
        Requires re-authentication with current password.
        """
        try:
            # 1. Verify current password by signing in
            # This ensures the user knows the current password
            auth = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": current_password}
            )
            
            if not auth.user:
                 raise ValueError("Invalid current password")

            # 2. Update to new password
            # We can use the admin api or the user context. 
            # Since we just signed in, we could use that session, but using the admin client 
            # (initialized in __init__) is fine as we just verified identity.
            self.supabase.auth.admin.update_user_by_id(
                auth.user.id, {"password": new_password}
            )
        except Exception as e:
            if "invalid info" in str(e).lower() or "login" in str(e).lower():
                 raise ValueError("Invalid current password")
            raise ValueError(f"Failed to change password: {str(e)}")

    async def request_password_reset(self, email: str) -> None:
        """
        Request password reset email via Supabase.

        Args:
            email: User email

        Note:
            Always returns success even if email doesn't exist (security practice).
            Supabase will send reset email if the email is registered.
        """
        try:
            # Supabase sends password reset email with magic link
            # The redirect URL should point to our frontend reset-password page
            redirect_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password"

            self.supabase.auth.reset_password_email(
                email, options={"redirect_to": redirect_url}
            )
        except Exception:
            # Silently fail - don't reveal if email exists
            pass

    async def reset_password_with_token(self, token: str, new_password: str) -> None:
        """
        Reset password using recovery token from email.

        Args:
            token: Recovery token from reset email
            new_password: New password to set

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            # Verify the recovery token and update password
            response = self.supabase.auth.verify_otp(
                {"token_hash": token, "type": "recovery"}
            )

            if not response.session:
                raise ValueError("Invalid or expired reset token")

            # Update password
            self.supabase.auth.update_user({"password": new_password})
        except Exception as e:
            raise ValueError(f"Failed to reset password: {str(e)}")

    async def delete_user(self, user_id: UUID) -> None:
        """
        Delete user from Supabase Auth and local DB.
        
        Args:
            user_id: The UUID of the user to delete
            
        Raises:
            ValueError: If deletion fails
        """
        try:
            # 1. Delete from Supabase Auth
            # We need to use the admin API which requires the service_role key
            # The client initialized in __init__ should have this key if configured correctly
            self.supabase.auth.admin.delete_user(str(user_id))
            
            # 2. Delete from local DB
            # We can use the repository to delete the user
            # Note: This assumes cascading deletes are set up in the DB for related records
            # If not, we might need to delete related records first
            await self.user_repo.delete(user_id)
            
        except Exception as e:
            raise ValueError(f"Failed to delete user: {str(e)}")
