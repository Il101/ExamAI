from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
    """Request to initiate password reset"""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request to reset password with token"""

    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)


class PasswordResetResponse(BaseModel):
    """Response for password reset operations"""

    message: str
