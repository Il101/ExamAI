from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.exceptions import AuthenticationException, ValidationException
from app.dependencies import get_auth_service, get_current_user
from app.domain.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
    ChangePasswordRequest,
)
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    PasswordResetResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.subscription_service import SubscriptionService
from app.dependencies import get_auth_service, get_current_user, get_subscription_service, oauth2_scheme

from app.core.rate_limiter import login_rate_limiter, general_rate_limiter, session_tracker
import hashlib

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(login_rate_limiter)]
)
async def register(
    request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register new user.

    - **email**: Valid email address
    - **password**: Minimum 8 characters, must include uppercase, lowercase, digit, and any non-alphanumeric char (e.g. !@#$%^&*()-_=+)
    - **full_name**: User's full name
    """

    try:
        user = await auth_service.register(
            email=request.email, password=request.password, full_name=request.full_name
        )

        return UserResponse.from_orm(user)

    except ValueError as e:
        raise ValidationException(str(e))


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(login_rate_limiter)])
async def login(
    request: LoginRequest, 
    auth_service: AuthService = Depends(get_auth_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Login with email and password.

    Returns JWT access token and refresh token.
    """

    auth_data = await auth_service.authenticate(request.email, request.password)

    if not auth_data:
        raise AuthenticationException("Invalid email or password")

    # Session limit enforcement
    try:
        access_token = auth_data["access_token"]
        user_id = str(auth_data["user"].id)
        session_id = hashlib.sha256(access_token.encode()).hexdigest()
        
        # Get plan limits
        subscription = await subscription_service.get_user_subscription(auth_data["user"].id)
        limits = subscription.get_limits()
        max_sessions = limits.get("max_simultaneous_sessions", 1)
        
        # Track session in Redis (Kick others if limit reached)
        await session_tracker.add_session(
            user_id=user_id,
            session_id=session_id,
            limit=max_sessions,
            ttl=settings.PERMANENT_SESSION_TTL
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to track session: {e}")
        # Fail open - let the user login even if Redis fails

    return TokenResponse(
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"],
        expires_in=auth_data.get("expires_in", 3600),
    )


@router.post("/refresh", response_model=TokenResponse, dependencies=[Depends(general_rate_limiter)])
async def refresh_token(
    request: RefreshTokenRequest, 
    auth_service: AuthService = Depends(get_auth_service),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
):
    """
    Refresh access token using refresh token.
    """

    auth_data = await auth_service.refresh_token(request.refresh_token)

    if not auth_data:
        raise AuthenticationException("Invalid or expired refresh token")

    # Sync session tracker with new access token
    try:
        access_token = auth_data["access_token"]
        user_id = str(auth_data["user"].id)
        session_id = hashlib.sha256(access_token.encode()).hexdigest()
        
        # Get plan limits
        subscription = await subscription_service.get_user_subscription(auth_data["user"].id)
        limits = subscription.get_limits()
        max_sessions = limits.get("max_simultaneous_sessions", 1)
        
        # Track session in Redis (Kick others if limit reached)
        await session_tracker.add_session(
            user_id=user_id,
            session_id=session_id,
            limit=max_sessions,
            ttl=settings.PERMANENT_SESSION_TTL
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to sync session on refresh: {e}")

    return TokenResponse(
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"],
        expires_in=auth_data.get("expires_in", 3600),
    )


@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(
    request: VerifyEmailRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Verify user email with verification token.
    """
    # Note: Supabase handles email verification automatically via link in email.
    # This endpoint might be used if we want to handle the callback manually,
    # but typically the frontend handles the deep link.

    # For now, we'll keep it as a placeholder or remove it if not needed.
    # If using Supabase, the user clicks a link that goes to the frontend,
    # which then might call an endpoint or just use the Supabase JS client.


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user profile.
    Requires authentication.
    """

    return UserResponse.from_orm(current_user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout current user.
    """
    try:
        session_id = hashlib.sha256(token.encode()).hexdigest()
        await session_tracker.remove_session(str(current_user.id), session_id)
    except Exception:
        pass

    return {"message": "Logged out successfully"}


@router.post("/forgot-password", response_model=PasswordResetResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Request password reset email.

    Sends password reset link to user's email if it exists.
    Always returns success for security (doesn't reveal if email exists).
    """
    await auth_service.request_password_reset(request.email)

    return PasswordResetResponse(
        message="If your email is registered, you will receive a password reset link."
    )


@router.post("/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    request: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Reset password using recovery token from email.

    - **token**: Recovery token from reset email
    - **new_password**: New password (minimum 8 characters)
    """
    try:
        await auth_service.reset_password_with_token(
            request.token, request.new_password
        )
        return PasswordResetResponse(
            message="Password reset successful. You can now log in."
        )
    except ValueError as e:
        raise ValidationException(str(e))


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(login_rate_limiter)]
)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Change password.
    Requires current password for security.
    """
    try:
        await auth_service.change_password(
            email=current_user.email,
            current_password=request.current_password,
            new_password=request.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
