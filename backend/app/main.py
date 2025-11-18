from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from datetime import datetime
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

from app.core.config import settings
from app.core.exceptions import AppException
from app.api.v1.router import api_router
from app.db.session import init_db, close_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for startup and shutdown"""
    # Startup
    print("🚀 Starting ExamAI Pro API...")
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    # Initialize Sentry (if production)
    if settings.ENVIRONMENT == "production" and settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[FastApiIntegration()],
            environment=settings.ENVIRONMENT,
            traces_sample_rate=0.1,
        )
        print("✅ Sentry initialized")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down...")
    await close_db()
    print("✅ Database connections closed")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered exam preparation platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
                "request_id": request.state.request_id if hasattr(request.state, "request_id") else None,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
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
        "environment": settings.ENVIRONMENT
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ExamAI Pro API",
        "version": settings.VERSION,
        "docs": "/api/docs"
    }
