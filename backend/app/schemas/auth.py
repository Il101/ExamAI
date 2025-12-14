from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """User registration request"""

    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        import re
        
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        # Accept any non-alphanumeric as a special character (covers Apple-generated passwords with dashes)
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character (e.g. !@#$%^&*()-_=+)")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "student@example.com",
                "password": "SecurePass123!",
                "full_name": "John Doe",
            }
        }


class LoginRequest(BaseModel):
    """User login request"""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int  # seconds


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""

    refresh_token: str


class VerifyEmailRequest(BaseModel):
    """Email verification request"""

    token: str


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        import re
        
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        # Accept any non-alphanumeric as a special character (covers Apple-generated passwords with dashes)
        if not re.search(r"[^A-Za-z0-9]", v):
            raise ValueError("Password must contain at least one special character (e.g. !@#$%^&*()-_=+)")
        return v
