from fastapi import APIRouter, Depends, Request, status

from app.core.exceptions import AuthenticationException, ValidationException
from app.dependencies import get_auth_service, get_current_user
from app.domain.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.schemas.password_reset import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    PasswordResetResponse,
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegisterRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register new user.

    - **email**: Valid email address
    - **password**: Minimum 8 characters, must include uppercase, lowercase, digit, special char
    - **full_name**: User's full name
    """

    try:
        user = await auth_service.register(
            email=request.email, password=request.password, full_name=request.full_name
        )

        return UserResponse.from_orm(user)

    except ValueError as e:
        raise ValidationException(str(e))


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password.

    Returns JWT access token and refresh token.
    """

    auth_data = await auth_service.authenticate(request.email, request.password)

    if not auth_data:
        raise AuthenticationException("Invalid email or password")

    return TokenResponse(
        access_token=auth_data["access_token"],
        refresh_token=auth_data["refresh_token"],
        expires_in=auth_data.get("expires_in", 3600),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest, auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    """

    auth_data = await auth_service.refresh_token(request.refresh_token)

    if not auth_data:
        raise AuthenticationException("Invalid or expired refresh token")

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
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout current user.
    """

    # In a real app, we might want to pass the access token to invalidate it on Supabase side if possible,
    # but Supabase logout is typically client-side or just invalidating the session.
    # Our AuthService.logout takes an access_token.

    # We need to extract the token from the request headers or context if we want to call Supabase logout.
    # For now, we'll just return success as the client should discard the token.

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
