from functools import lru_cache
from typing import List, Literal, Optional
import json

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central application configuration.
    All settings from .env file or environment variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

    # Application
    APP_NAME: str = "ExamAI Pro"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://exam-ai-hzzw.vercel.app",  # Production URL
        "https://exam-ai-hzzw-5wcpiuwsd-ilias-projects-774295b7.vercel.app",
        "https://exam-ai-hzzw-oy52erqht-ilias-projects-774295b7.vercel.app"
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        """Parse ALLOWED_ORIGINS from string (JSON or comma-separated) or list"""
        if isinstance(v, str):
            # Try JSON first
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fall back to comma-separated
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # CORS Regex for Vercel Deployments (both production and previews)
    # Matches: https://exam-ai-hzzw.vercel.app and https://exam-ai-*-ilias-projects-774295b7.vercel.app
    CORS_ORIGIN_REGEX: str = r"https://exam-ai-[a-z0-9-]*\.vercel\.app"

    # AI Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-1.5-flash"  # For exam generation (quality)
    GEMINI_QUIZ_MODEL: str = "gemini-2.5-flash-lite"  # For flashcards/MCQs (speed + economy)
    GEMINI_CHAT_MODEL: str = "gemini-1.5-flash-8b"  # For chat tutor (speed + economy)
    GEMINI_FALLBACK_MODEL: str = "gemini-1.5-flash"  # Fallback for 503 errors
    GEMINI_QUIZ_FALLBACK_MODEL: str = "gemini-1.5-flash-8b"  # Fallback for quiz generation
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    LLM_PROVIDER: Literal["gemini", "openai"] = "gemini"  # Which LLM to use
    PROMPTS_DIR: str = "app/prompts"
    MAX_TOPICS: Optional[int] = None  # None = let AI decide based on content

    # Security
    SECRET_KEY: str  # min 32 chars, used for JWT
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = ""

    # Supabase
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""  # Service_role key for admin tasks
    SUPABASE_ANON_KEY: str = ""  # Public anon key for user-facing auth operations
    SUPABASE_BUCKET: str = "exam-files"  # Storage bucket for exam files

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @model_validator(mode="after")
    def set_celery_urls(self):
        """Ensure Celery URLs use REDIS_URL if not explicitly set"""
        if not self.CELERY_BROKER_URL:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if not self.CELERY_RESULT_BACKEND:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        return self

    # Sentry
    SENTRY_DSN: Optional[str] = None

    # Email
    EMAIL_FROM: str = "noreply@examai.pro"
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None

    # SendGrid
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "noreply@examai.pro"
    
    # Notification Settings
    NOTIFICATION_PROVIDER: Literal["sendgrid", "smtp", "mock"] = "sendgrid"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID_PRO: str = ""  # price_xxx from Stripe Dashboard
    STRIPE_PRICE_ID_PREMIUM: str = ""  # price_xxx from Stripe Dashboard

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()
