# Stage 10: Production Deployment & DevOps

**Time:** 3-4 days  
**Goal:** Deploy application to production with monitoring, logging, and CI/CD

## 10.1 Deployment Architecture

### Infrastructure Overview
```
┌─────────────────────────────────────────────────────────┐
│                     CloudFlare CDN                      │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┴──────────────┐
        │                            │
┌───────▼────────┐          ┌────────▼────────┐
│  Vercel         │          │  Railway.app    │
│  (Frontend)     │          │  (Backend)      │
│  - Next.js      │◄────────►│  - FastAPI      │
│  - Static       │          │  - Celery       │
└─────────────────┘          │  - Redis        │
                             └────────┬────────┘
                                      │
                             ┌────────▼────────┐
                             │   Supabase      │
                             │  - PostgreSQL   │
                             │  - Auth         │
                             │  - Storage      │
                             └─────────────────┘
```

### Components
- **Frontend**: Vercel (auto-deploy from GitHub)
- **Backend**: Railway.app (Docker containers)
- **Database**: Supabase (managed PostgreSQL) or Railway Postgres
- **Cache/Queue**: Redis on Railway
- **CDN**: CloudFlare (Future)
- **Monitoring**: Sentry
- **Logs**: Railway logs + CloudWatch

*Note: Domain is not yet purchased. Will use Railway/Vercel default subdomains for MVP.*

---

## 10.2 Docker Configuration

### Step 10.2.1: Backend Dockerfile
```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 10.2.2: Docker Compose (Production)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
      - ENVIRONMENT=production
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=4
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - redis
    restart: unless-stopped
  
  celery_beat:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.tasks.celery_app beat --loglevel=info
    environment:
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - redis
    restart: unless-stopped
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis_data:
```

---

## 10.3 Environment Configuration

### Step 10.3.1: Production Environment Variables
```bash
# .env.production (NEVER COMMIT THIS)

# Application
ENVIRONMENT=production
SECRET_KEY=<generate-with-openssl-rand-hex-32>
FRONTEND_URL=https://examai-pro.vercel.app

# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres:[PASSWORD]@[HOST]:5432/postgres
SUPABASE_URL=https://[PROJECT].supabase.co
SUPABASE_ANON_KEY=<supabase-anon-key>
SUPABASE_SERVICE_KEY=<supabase-service-key>

# Redis (Railway)
REDIS_URL=redis://default:[PASSWORD]@[HOST]:6379
CELERY_BROKER_URL=redis://default:[PASSWORD]@[HOST]:6379/0
CELERY_RESULT_BACKEND=redis://default:[PASSWORD]@[HOST]:6379/0

# LLM
GEMINI_API_KEY=<google-gemini-api-key>
GEMINI_MODEL=gemini-2.0-flash-exp
LLM_PROVIDER=gemini

# Email (SendGrid)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=<sendgrid-api-key>
SMTP_TLS=true
EMAIL_FROM=noreply@examai-pro.com

# Monitoring
SENTRY_DSN=<sentry-dsn>
SENTRY_ENVIRONMENT=production

# Security
CORS_ORIGINS=https://examai-pro.vercel.app
ALLOWED_HOSTS=api.examai-pro.com,*.railway.app

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

### Step 10.3.2: Railway Configuration
```toml
# railway.toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
healthcheckPath = "/health"
healthcheckTimeout = 100

[[services]]
name = "backend"
type = "web"

[[services.ports]]
port = 8000
protocol = "HTTP"

[[services]]
name = "celery-worker"
type = "worker"

[[services]]
name = "redis"
type = "redis"
```

---

## 10.4 Database Migrations

### Step 10.4.1: Migration Script
```python
# backend/scripts/migrate.py
"""
Run database migrations in production.
Usage: python scripts/migrate.py
"""
import asyncio
from alembic import command
from alembic.config import Config

def run_migrations():
    """Run Alembic migrations"""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✅ Migrations completed successfully")

if __name__ == "__main__":
    run_migrations()
```

### Step 10.4.2: Pre-Deploy Migration Check
```bash
# scripts/deploy-check.sh
#!/bin/bash

echo "🔍 Checking database migrations..."

# Check for pending migrations
python -c "
from alembic import command
from alembic.config import Config

config = Config('alembic.ini')
command.check(config)
"

if [ $? -eq 0 ]; then
    echo "✅ No pending migrations"
else
    echo "❌ Pending migrations found! Run migrations before deploying."
    exit 1
fi
```

---

## 10.5 Monitoring & Logging

### Step 10.5.1: Sentry Integration
```python
# backend/app/core/monitoring.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from app.core.config import settings


def init_monitoring():
    """Initialize Sentry monitoring"""
    if settings.ENVIRONMENT == "production" and settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.1,  # 10% of requests for performance monitoring
            profiles_sample_rate=0.1,
            send_default_pii=False,  # Don't send PII
            before_send=filter_sensitive_data,
        )


def filter_sensitive_data(event, hint):
    """Remove sensitive data before sending to Sentry"""
    # Remove password fields
    if 'request' in event:
        if 'data' in event['request']:
            data = event['request']['data']
            if isinstance(data, dict):
                for key in ['password', 'token', 'api_key']:
                    if key in data:
                        data[key] = '[Filtered]'
    
    return event
```

### Step 10.5.2: Structured Logging
```python
# backend/app/core/logging.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured JSON logging for production"""
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    
    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger


# Usage in app
logger = logging.getLogger(__name__)
logger.info("User logged in", extra={"user_id": str(user.id), "email": user.email})
```

---

## 10.6 Health Checks

### Step 10.6.1: Health Check Endpoint
```python
# backend/app/api/v1/endpoints/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis import Redis

from app.db.session import get_db_session
from app.tasks.celery_app import celery_app

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "service": "examai-backend"
    }


@router.get("/health/detailed")
async def detailed_health_check(
    db: AsyncSession = Depends(get_db_session)
):
    """Detailed health check with dependency checks"""
    
    health = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check Redis
    try:
        celery_app.backend.client.ping()
        health["checks"]["redis"] = "healthy"
    except Exception as e:
        health["checks"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    # Check Celery workers
    try:
        stats = celery_app.control.inspect().stats()
        if stats:
            health["checks"]["celery_workers"] = "healthy"
        else:
            health["checks"]["celery_workers"] = "no workers available"
            health["status"] = "degraded"
    except Exception as e:
        health["checks"]["celery_workers"] = f"unhealthy: {str(e)}"
        health["status"] = "unhealthy"
    
    return health
```

---

## 10.7 CI/CD Pipeline

### Step 10.7.1: GitHub Actions Deployment
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Run tests
        run: |
          cd backend
          pip install -r requirements.txt
          pip install -r requirements-test.txt
          pytest tests/ -v --cov=app
  
  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Railway
        uses: bervProject/railway-deploy@main
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
          service: backend
  
  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

---

## 10.8 Security Hardening

### Step 10.8.1: Security Headers
```python
# backend/app/core/security.py
from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
```

### Step 10.8.2: Rate Limiting
```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["60/minute"],
    storage_uri="redis://localhost:6379"
)

# Add to FastAPI app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Usage on endpoints
@router.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
    ...
```

---

## 10.9 Backup Strategy

### Step 10.9.1: Database Backups
```bash
# scripts/backup-db.sh
#!/bin/bash

# Daily database backup script
# Add to cron: 0 2 * * * /path/to/backup-db.sh

BACKUP_DIR="/backups/examai"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/examai_backup_$DATE.sql.gz"

# Create backup directory if not exists
mkdir -p $BACKUP_DIR

# Run pg_dump and compress
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h $DB_HOST \
    -U $DB_USER \
    -d $DB_NAME \
    | gzip > $BACKUP_FILE

# Upload to S3 or cloud storage
aws s3 cp $BACKUP_FILE s3://examai-backups/database/

# Keep only last 30 days of backups locally
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "✅ Backup completed: $BACKUP_FILE"
```

---

## 10.10 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Database migrations reviewed
- [ ] Environment variables configured
- [ ] Secrets rotated
- [ ] Dependencies updated
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Backup strategy verified

### Deployment
- [ ] Deploy to staging first
- [ ] Run smoke tests on staging
- [ ] Run database migrations
- [ ] Deploy backend
- [ ] Deploy frontend
- [ ] Verify health checks
- [ ] Test critical flows

### Post-Deployment
- [ ] Monitor error rates (Sentry)
- [ ] Check application logs
- [ ] Verify Celery workers running
- [ ] Test user registration/login
- [ ] Test exam generation
- [ ] Monitor database performance
- [ ] Check API response times
- [ ] Verify email delivery

### Rollback Plan
```bash
# If deployment fails, rollback to previous version

# Railway
railway rollback --service backend

# Vercel
vercel rollback https://examai-pro.vercel.app
```

---

## 10.11 Monitoring Dashboard

### Key Metrics to Track
- **Availability**: Uptime percentage (target: 99.9%)
- **Response Time**: P50, P95, P99 latencies
- **Error Rate**: 4xx and 5xx errors
- **Database**: Connection pool usage, query time
- **Celery**: Queue length, task duration
- **Cost**: Daily LLM spend per user
- **Usage**: Active users, exams created, reviews completed

### Alerts
- **Critical**: Database down, Redis down, error rate >5%
- **Warning**: High latency (>1s), queue backup (>100 tasks)
- **Info**: New deployment, high traffic

---

## 10.12 Best Practices Summary

✅ **DO**:
- Use environment variables for all config
- Enable HTTPS everywhere
- Implement rate limiting
- Log structured JSON
- Set up monitoring and alerts
- Use health checks
- Automate backups
- Test deployments on staging first

❌ **DON'T**:
- Commit secrets to git
- Use default passwords
- Skip database migrations
- Deploy without tests
- Ignore security updates
- Run as root in containers

---

## 🎉 Deployment Complete!

Your ExamAI Pro application is now:
- ✅ Deployed to production
- ✅ Monitored with Sentry
- ✅ Auto-deploying from GitHub
- ✅ Secured with HTTPS and security headers
- ✅ Backed up daily
- ✅ Scaled with Celery workers
- ✅ Ready for users!

**Next Steps**:
1. Set up custom domain
2. Configure email templates
3. Implement analytics
4. Add payment integration (Stripe)
5. Build mobile app
6. Scale infrastructure as needed
