from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
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
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("⚠️  App will start but database operations will fail")

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
    swallow_errors=settings.ENVIRONMENT == "production",  # Don't fail if Redis is unavailable in production
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

# CORS middleware - must be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Security headers (production only)
if settings.ENVIRONMENT == "production":
    app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# FastAPI validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors with CORS headers"""
    response = JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Validation error",
                "details": exc.errors() if hasattr(exc, 'errors') else str(exc),
                "request_id": (
                    request.state.request_id
                    if hasattr(request.state, "request_id")
                    else None
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )
    # Ensure CORS headers are added
    origin = request.headers.get("origin")
    if origin and origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# Global exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions"""
    response = JSONResponse(
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
    # Ensure CORS headers are added even for errors
    origin = request.headers.get("origin")
    if origin and origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# Global exception handler for all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions with CORS headers"""
    import traceback
    import logging
    
    logger = logging.getLogger(__name__)
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    response = JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "Internal server error",
                "details": str(exc) if settings.DEBUG else None,
                "request_id": (
                    request.state.request_id
                    if hasattr(request.state, "request_id")
                    else None
                ),
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )
    # Ensure CORS headers are added even for errors
    origin = request.headers.get("origin")
    if origin and origin in settings.ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


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


# Debug endpoint for CORS configuration
@app.get("/debug/cors")
async def debug_cors():
    """Debug endpoint to check CORS configuration"""
    return {
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "frontend_url": settings.FRONTEND_URL,
        "environment": settings.ENVIRONMENT,
    }


# Debug endpoint for DB inspection
@app.get("/debug/db")
async def debug_db():
    """Debug endpoint to check DB schema"""
    from sqlalchemy import text
    from app.db.session import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        # Check alembic version
        try:
            result = await session.execute(text("SELECT * FROM alembic_version"))
            version = result.scalar_one_or_none()
        except Exception as e:
            version = str(e)
        
        # Check columns
        try:
            result_cols = await session.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"
            ))
            columns = [row[0] for row in result_cols.fetchall()]
            
            # Check for NULLs
            result_nulls = await session.execute(text(
                "SELECT COUNT(*) FROM users WHERE notification_exam_ready IS NULL"
            ))
            null_count = result_nulls.scalar()
        except Exception as e:
            columns = str(e)
            null_count = -1
            
        return {
            "alembic_version": version,
            "columns": columns,
            "has_notification_exam_ready": "notification_exam_ready" in columns if isinstance(columns, list) else False,
            "null_count": null_count
        }

