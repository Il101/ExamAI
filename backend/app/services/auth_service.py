from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID
from supabase import create_client, Client
from jose import jwt, JWTError
from app.domain.user import User
from app.repositories.user_repository import UserRepository
from app.core.config import settings


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
            auth_response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"full_name": full_name}},
                }
            )

            if not auth_response.user:
                raise ValueError("Registration failed: No user returned from Supabase")

            user_id = UUID(auth_response.user.id)

            # 2. Create user profile in our DB (public.users)
            # Note: In a real Supabase setup, you might use a Trigger for this.
            # But doing it here ensures our domain logic is applied.

            user = User(
                id=user_id,
                email=email.lower().strip(),
                full_name=full_name.strip(),
                is_verified=False,  # Supabase handles verification
            )

            created = await self.user_repo.create(user)

            return created

        except Exception as e:
            # Map Supabase errors to ValueError
            raise ValueError(f"Registration failed: {str(e)}")

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

        except Exception:
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
        except Exception:
            return None

    # Token Verification

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
        raise NotImplementedError("Email verification is handled by Supabase directly")
