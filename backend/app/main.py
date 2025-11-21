from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import setup_logging
from app.core.monitoring import init_monitoring
from app.db.session import close_db, init_db
from app.middleware.security import RequestLoggingMiddleware, SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    print("🚀 Starting ExamAI Pro API...")

    # Initialize logging
    setup_logging(log_level="INFO" if settings.ENVIRONMENT == "production" else "DEBUG")
    print("✅ Logging configured")

    # Initialize monitoring
    init_monitoring()
    if settings.SENTRY_DSN:
        print("✅ Sentry monitoring initialized")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    yield

    # Shutdown
    print("🛑 Shutting down...")
    await close_db()
    print("✅ Database connections closed")


# Custom rate limit key function that considers user tier
async def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on user and their subscription tier.
    Returns identifier for rate limiting (IP or user_id).
    """
    # Try to get user from request state (set by auth middleware)
    if hasattr(request.state, "user") and request.state.user:
        user = request.state.user
        user_id = str(user.id)
        # Use user ID as key for authenticated users
        return f"user:{user_id}"
    
    # Fall back to IP-based rate limiting for unauthenticated requests
    return get_remote_address(request)


# Initialize rate limiter with Redis storage
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=settings.REDIS_URL,
    default_limits=["200/hour"],  # Conservative default
    headers_enabled=True,
    swallow_errors=False,  # Raise errors in development
)



# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered exam preparation platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers (production only)
if settings.ENVIRONMENT == "production":
    app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request, exc: AppException):
    """Handle custom application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "request_id": (
                    request.state.request_id
                    if hasattr(request.state, "request_id")
                    else None
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ExamAI Pro API",
        "version": settings.VERSION,
        "docs": "/api/docs",
    }
