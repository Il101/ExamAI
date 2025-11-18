# Deployment Guide — ExamAI Pro

## Overview

Comprehensive deployment and infrastructure guide for ExamAI Pro, covering CI/CD pipelines, environment configurations, Docker containerization, monitoring, and rollback procedures.

**Infrastructure Stack:**
- **Backend Hosting:** Railway.app
- **Database:** Supabase (PostgreSQL + Auth + Storage)
- **Frontend Hosting:** Vercel (Next.js)
- **Container Orchestration:** Docker (Railway)
- **CI/CD:** GitHub Actions
- **Monitoring:** Sentry (errors), PostHog (analytics)
- **File Storage:** Supabase Storage
- **CDN:** CloudFlare

---

## Table of Contents

1. [Environment Strategy](#environment-strategy)
2. [Infrastructure Architecture](#infrastructure-architecture)
3. [Docker Configuration](#docker-configuration)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Deployment Process](#deployment-process)
6. [Environment Variables](#environment-variables)
7. [Database Migrations](#database-migrations)
8. [Monitoring & Alerting](#monitoring--alerting)
9. [Rollback Procedures](#rollback-procedures)
10. [Security Considerations](#security-considerations)
11. [Scaling Strategy](#scaling-strategy)

---

## Environment Strategy

### Three-Tier Environment Setup

```
Development (Local)
    ↓
Staging (Pre-production)
    ↓
Production (Live)
```

### Environment Comparison

| Aspect | Development | Staging | Production |
|--------|-------------|---------|------------|
| **URL** | `localhost:3000` | `staging.examai.com` | `app.examai.com` |
| **Database** | Supabase (free tier) | Supabase (free tier) | Supabase (Pro) |
| **Backend** | Local FastAPI | Railway (Hobby) | Railway (Developer+) |
| **Frontend** | Local Next.js | Vercel (Preview) | Vercel (Production) |
| **LLM Model** | `gemini-1.5-flash` | `gemini-1.5-flash` | `gemini-1.5-pro` |
| **Storage** | Supabase Storage (local) | Supabase Storage (staging) | Supabase Storage (prod) |
| **Email** | Console logs | SendGrid (test) | SendGrid (live) |
| **Analytics** | Disabled | PostHog (staging) | PostHog (production) |
| **SSL** | No | Yes (Auto) | Yes (CloudFlare) |
| **Auto-deploy** | No | Yes (on `develop` push) | Manual approval |
| **Backup** | No | Daily (Supabase) | Hourly (Supabase) |

---

## Infrastructure Architecture

### MVP Architecture (< 1,000 users)

```
┌─────────────────────────────────────────────────────────┐
│                     CloudFlare CDN                       │
│                  (SSL, WAF, DDoS Protection)             │
└───────────────────────┬─────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│   Vercel (Next.js)  │  │  Railway (FastAPI) │  │  Supabase         │
│                  │  │                  │  │                  │
│ - SSR/SSG        │  │ - Docker         │  │ - PostgreSQL     │
│ - API Routes     │  │ - Auto-deploy    │  │ - Auth           │
│ - CDN Edge       │  │ - Health checks  │  │ - Storage        │
└────────┬─────────┘  └────────┬─────────┘  │ - Row Level      │
         │                       │           │   Security (RLS) │
         └───────────┬───────────┘           └──────────────────┘
                     │
                     ▼
         ┌──────────────────────────────┐
         │     Upstash Redis (Cache)      │
         │    - Session storage         │
         │    - Rate limiting           │
         └──────────────────────────────┘
```

**Cost Estimate (MVP):**
- Vercel: $0 (Hobby tier)
- Railway: $5-20/month (Hobby/Developer)
- Supabase: $0-25/month (Free/Pro tier)
- Upstash Redis: $0 (Free tier)
- **Total: $5-45/month**
        ┌───────────────┴───────────────┐
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│   Web Server 1   │          │   Web Server 2   │
│   (Docker)       │          │   (Docker)       │
│                  │          │                  │
│ - Next.js        │          │ - Next.js        │
│ - FastAPI        │          │ - FastAPI        │
└────────┬─────────┘          └─────────┬────────┘
         │                              │
         └──────────────┬───────────────┘
                        ▼
         ┌──────────────────────────────┐
         │    PostgreSQL (Managed)      │
         │    - Primary + Read Replica  │
         └──────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │       Redis (Cache)          │
         │    - Session storage         │
         │    - Rate limiting           │
         └──────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │      S3 / R2 Storage         │
         │    - File uploads            │
         │    - Static assets           │
         └──────────────────────────────┘
                        │
                        ▼
         ┌──────────────────────────────┐
         │   External Services          │
         │  - Gemini API (Google)       │
         │  - Stripe (Payments)         │
         │  - SendGrid (Email)          │
         └──────────────────────────────┘
```

### Scaled Architecture (> 10,000 users)

```
CloudFlare CDN
    ↓
AWS ALB / GCP Load Balancer
    ↓
Kubernetes Cluster
    ├── Frontend Pods (Next.js) — Autoscaling 2-10 pods
    ├── Backend Pods (FastAPI) — Autoscaling 3-20 pods
    └── Worker Pods (Celery) — Background jobs
    ↓
PostgreSQL (Multi-region, HA)
Redis Cluster (Sentinel mode)
S3 / R2 (Multi-region)
```

---

## Docker Configuration

### Project Structure

```
examai/
├── docker/
│   ├── Dockerfile.backend       # FastAPI
│   ├── Dockerfile.frontend      # Next.js
│   ├── Dockerfile.nginx         # Reverse proxy
│   └── docker-compose.yml       # Local development
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── alembic/
├── frontend/
│   ├── app/
│   ├── package.json
│   └── next.config.js
└── .github/
    └── workflows/
```

### Dockerfile.backend (FastAPI)

```dockerfile
# Multi-stage build for smaller image size
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY backend/ .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Dockerfile.frontend (Next.js)

```dockerfile
# Dependencies stage
FROM node:20-alpine AS deps

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --only=production

# Builder stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .

# Build Next.js app
ENV NEXT_TELEMETRY_DISABLED 1
RUN npm run build

# Runner stage
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

### docker-compose.yml (Development)

```yaml
version: '3.9'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: examai_postgres
    environment:
      POSTGRES_DB: examai_dev
      POSTGRES_USER: examai
      POSTGRES_PASSWORD: dev_password_change_me
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U examai"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: examai_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  # Backend (FastAPI)
  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    container_name: examai_backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://examai:dev_password_change_me@postgres:5432/examai_dev
      - REDIS_URL=redis://redis:6379/0
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - ENVIRONMENT=development
    volumes:
      - ./backend:/app
      - ./uploads:/app/uploads  # File storage
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  # Frontend (Next.js)
  frontend:
    build:
      context: .
      dockerfile: docker/Dockerfile.frontend
    container_name: examai_frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_STRIPE_PUBLIC_KEY=${STRIPE_PUBLIC_KEY}
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    depends_on:
      - backend
    command: npm run dev

  # NGINX Reverse Proxy (Optional for local testing)
  nginx:
    image: nginx:alpine
    container_name: examai_nginx
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend

volumes:
  postgres_data:
  redis_data:
```

### NGINX Configuration

```nginx
# docker/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # Backend API
        location /api {
            rewrite ^/api/(.*) /$1 break;
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Health check
        location /health {
            access_log off;
            return 200 "OK\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

**.github/workflows/deploy-staging.yml**

```yaml
name: Deploy to Staging

on:
  push:
    branches:
      - develop

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run backend tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml

      - name: Set up Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - name: Run frontend tests
        run: |
          cd frontend
          npm test

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  build:
    name: Build Docker Images
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata (tags, labels)
        id: meta-backend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-backend
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-

      - name: Build and push backend image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.backend
          push: true
          tags: ${{ steps.meta-backend.outputs.tags }}
          labels: ${{ steps.meta-backend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Extract metadata for frontend
        id: meta-frontend
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-frontend
          tags: |
            type=ref,event=branch
            type=sha,prefix={{branch}}-

      - name: Build and push frontend image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: docker/Dockerfile.frontend
          push: true
          tags: ${{ steps.meta-frontend.outputs.tags }}
          labels: ${{ steps.meta-frontend.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy to Staging
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.examai.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Configure SSH
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.STAGING_SSH_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.STAGING_HOST }} >> ~/.ssh/known_hosts

      - name: Deploy to staging server
        run: |
          ssh ${{ secrets.STAGING_USER }}@${{ secrets.STAGING_HOST }} << 'EOF'
            cd /opt/examai
            
            # Pull latest images
            docker-compose pull
            
            # Run database migrations
            docker-compose run --rm backend alembic upgrade head
            
            # Restart services with zero-downtime
            docker-compose up -d --no-deps --build backend frontend
            
            # Health check
            sleep 10
            curl -f http://localhost:8000/health || exit 1
            curl -f http://localhost:3000 || exit 1
            
            # Cleanup old images
            docker image prune -f
          EOF

      - name: Notify Slack
        if: always()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'Staging deployment ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Production Deployment Workflow

**.github/workflows/deploy-production.yml**

```yaml
name: Deploy to Production

on:
  push:
    tags:
      - 'v*.*.*'  # Trigger on version tags (e.g., v1.0.0)

jobs:
  test:
    name: Run Full Test Suite
    runs-on: ubuntu-latest
    # ... (same as staging)

  build:
    name: Build Production Images
    needs: test
    runs-on: ubuntu-latest
    # ... (same as staging, but with version tags)

  deploy:
    name: Deploy to Production
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://app.examai.com

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Deploy to production (Blue-Green)
        run: |
          # Deploy to "green" environment first
          # Test green environment
          # Switch traffic from blue to green
          # Keep blue as rollback option

      - name: Run smoke tests
        run: |
          curl -f https://app.examai.com/health
          # Add more smoke tests

      - name: Notify team
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: '🚀 Production deployment ${{ github.ref_name }} ${{ job.status }}'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## Deployment Process

### Manual Deployment Steps

#### 1. Pre-Deployment Checklist

```bash
# ✅ Pre-deployment checklist
- [ ] All tests passing (CI green)
- [ ] Database migrations tested in staging
- [ ] No breaking API changes (or versioned)
- [ ] Environment variables updated
- [ ] Backups verified (< 24h old)
- [ ] Rollback plan documented
- [ ] Team notified (deployment window)
- [ ] Monitoring dashboards open
```

#### 2. Staging Deployment

```bash
# SSH into staging server
ssh user@staging.examai.com

# Navigate to app directory
cd /opt/examai

# Pull latest code
git pull origin develop

# Pull Docker images
docker-compose pull

# Run database migrations (with backup)
docker-compose run --rm backend alembic upgrade head

# Restart services
docker-compose up -d --force-recreate

# Verify health
curl http://localhost:8000/health
curl http://localhost:3000

# Check logs
docker-compose logs -f --tail=100
```

#### 3. Production Deployment (Blue-Green)

```bash
# Option A: Manual Blue-Green Deployment
# Current: Blue (live)
# Deploy: Green (new version)

# 1. Deploy to Green environment
ssh user@prod-green.examai.com
cd /opt/examai
git pull origin main
docker-compose pull
docker-compose run --rm backend alembic upgrade head
docker-compose up -d

# 2. Smoke test Green
curl -f https://green.examai.com/health
# Run critical API tests

# 3. Switch Load Balancer traffic: Blue → Green
# (CloudFlare, AWS ALB, or manual NGINX config)

# 4. Monitor for 30 minutes
# Check error rates, response times, user complaints

# 5. If successful: Keep Green as primary
# 6. If issues: Rollback to Blue (see below)
```

```bash
# Option B: Rolling Deployment (Kubernetes)
kubectl set image deployment/examai-backend \
  backend=ghcr.io/il101/examai-backend:v1.2.0

kubectl rollout status deployment/examai-backend

# Monitor rollout
kubectl get pods -w
```

---

## Environment Variables

### Development (.env.development)

```bash
# Backend
DATABASE_URL=postgresql://examai:dev_password@localhost:5432/examai_dev
REDIS_URL=redis://localhost:6379/0
GEMINI_API_KEY=AIza...
JWT_SECRET=dev_secret_change_in_production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=15

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_...

# Email
EMAIL_PROVIDER=console  # Log emails to console
SENDGRID_API_KEY=

# Storage
STORAGE_BACKEND=local
UPLOAD_DIR=/app/uploads

# Analytics
POSTHOG_API_KEY=
SENTRY_DSN=
ENVIRONMENT=development
```

### Staging (.env.staging)

```bash
# Backend
DATABASE_URL=postgresql://examai:xxx@staging-db.examai.com:5432/examai_staging
REDIS_URL=redis://staging-redis.examai.com:6379/0
GEMINI_API_KEY=${GEMINI_API_KEY_STAGING}
JWT_SECRET=${JWT_SECRET_STAGING}

# Frontend
NEXT_PUBLIC_API_URL=https://api-staging.examai.com
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_test_...

# Email
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=${SENDGRID_API_KEY}
EMAIL_FROM=no-reply@staging.examai.com

# Storage
STORAGE_BACKEND=s3
S3_BUCKET=examai-staging-uploads
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_KEY}

# Analytics
POSTHOG_API_KEY=${POSTHOG_STAGING_KEY}
SENTRY_DSN=${SENTRY_DSN}
ENVIRONMENT=staging
```

### Production (.env.production)

```bash
# Backend
DATABASE_URL=${DATABASE_URL_PRODUCTION}  # From secret manager
REDIS_URL=${REDIS_URL_PRODUCTION}
GEMINI_API_KEY=${GEMINI_API_KEY_PRODUCTION}
JWT_SECRET=${JWT_SECRET_PRODUCTION}  # Strong random secret

# Frontend
NEXT_PUBLIC_API_URL=https://api.examai.com
NEXT_PUBLIC_STRIPE_PUBLIC_KEY=pk_live_...

# Email
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=${SENDGRID_API_KEY_PRODUCTION}
EMAIL_FROM=no-reply@examai.com

# Storage
STORAGE_BACKEND=s3
S3_BUCKET=examai-production-uploads
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_PRODUCTION}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_KEY_PRODUCTION}
CDN_URL=https://cdn.examai.com

# Analytics
POSTHOG_API_KEY=${POSTHOG_PRODUCTION_KEY}
SENTRY_DSN=${SENTRY_DSN_PRODUCTION}
ENVIRONMENT=production

# Security
ALLOWED_ORIGINS=https://app.examai.com,https://examai.com
RATE_LIMIT_ENABLED=true
CORS_ENABLED=true
```

### Secret Management

**Option 1: GitHub Secrets (for CI/CD)**

```bash
# Set secrets in GitHub repo settings
gh secret set GEMINI_API_KEY_PRODUCTION --body "AIza..."
gh secret set DATABASE_URL_PRODUCTION --body "postgresql://..."
```

**Option 2: Cloud Secret Manager**

```bash
# Google Cloud Secret Manager
gcloud secrets create gemini-api-key --data-file=secret.txt

# AWS Secrets Manager
aws secretsmanager create-secret \
  --name examai/production/gemini-api-key \
  --secret-string "AIza..."
```

**Option 3: HashiCorp Vault (Advanced)**

```bash
# Store secret in Vault
vault kv put secret/examai/production \
  gemini_api_key="AIza..." \
  database_url="postgresql://..."

# Retrieve in application
vault kv get -field=gemini_api_key secret/examai/production
```

---

## Database Migrations

### Alembic Setup

**Initial setup:**

```bash
cd backend
alembic init alembic
```

**alembic.ini configuration:**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/dbname  # Overridden by env.py
```

**alembic/env.py:**

```python
from sqlalchemy import engine_from_config, pool
from app.database import Base
from app.models import *  # Import all models
import os

config.set_main_option('sqlalchemy.url', os.getenv('DATABASE_URL'))

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=Base.metadata
        )

        with context.begin_transaction():
            context.run_migrations()
```

### Migration Workflow

```bash
# 1. Create migration (auto-generate from models)
alembic revision --autogenerate -m "Add subscriptions table"

# 2. Review generated migration
cat alembic/versions/abc123_add_subscriptions_table.py

# 3. Test migration locally
alembic upgrade head

# 4. Test rollback
alembic downgrade -1

# 5. Commit migration file to git
git add alembic/versions/
git commit -m "Add subscriptions table migration"

# 6. Deploy to staging (via CI/CD)
# Migration runs automatically in deploy.yml

# 7. Verify in staging
ssh staging.examai.com
docker-compose run --rm backend alembic current

# 8. Deploy to production (with backup)
ssh production.examai.com
# Backup before migration (see below)
docker-compose run --rm backend alembic upgrade head
```

### Pre-Migration Backup

```bash
# Automated backup before migration
#!/bin/bash
# scripts/backup_before_migration.sh

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="backup_pre_migration_${TIMESTAMP}.sql"

echo "Creating backup: $BACKUP_FILE"
pg_dump $DATABASE_URL > /backups/$BACKUP_FILE

# Verify backup
if [ $? -eq 0 ]; then
    echo "✅ Backup created successfully"
    gzip /backups/$BACKUP_FILE
    echo "✅ Backup compressed"
else
    echo "❌ Backup failed!"
    exit 1
fi

# Upload to S3
aws s3 cp /backups/${BACKUP_FILE}.gz s3://examai-backups/migrations/
echo "✅ Backup uploaded to S3"
```

---

## Monitoring & Alerting

### Health Checks

**Backend health endpoint:**

```python
# app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
import redis

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "database": "unknown",
        "redis": "unknown",
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check database
    try:
        db.execute("SELECT 1")
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["database"] = f"error: {str(e)}"
    
    # Check Redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["redis"] = f"error: {str(e)}"
    
    return health_status
```

### Prometheus Metrics

```python
# app/middleware/metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_users = Gauge(
    'active_users',
    'Number of active users'
)

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    http_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response
```

### Grafana Dashboard

**Key Metrics to Monitor:**

1. **Application Metrics**
   - Request rate (requests/sec)
   - Response time (p50, p95, p99)
   - Error rate (4xx, 5xx)
   - Active users

2. **Infrastructure Metrics**
   - CPU usage (%)
   - Memory usage (%)
   - Disk I/O
   - Network I/O

3. **Database Metrics**
   - Connection pool utilization
   - Query duration
   - Slow query count
   - Replication lag

4. **Business Metrics**
   - New signups/day
   - AI summaries generated/day
   - Review sessions completed/day
   - Subscription conversions

### Alerting Rules

**PagerDuty / Slack Alerts:**

```yaml
# alerting/rules.yml
groups:
  - name: examai_critical
    interval: 1m
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/sec"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"

      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High response time (p95 > 2s)"

      - alert: LowDiskSpace
        expr: node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Disk space below 10%"
```

---

## Rollback Procedures

### Scenario 1: Bad Deployment (Code Issue)

**Symptoms:**
- Increased error rate
- Failed health checks
- User complaints

**Rollback Steps:**

```bash
# 1. Immediate rollback (Docker)
ssh production.examai.com
cd /opt/examai

# Check current running version
docker-compose ps

# Rollback to previous image
docker-compose down
docker tag examai-backend:previous examai-backend:latest
docker-compose up -d

# Verify health
curl http://localhost:8000/health

# 2. Rollback via Load Balancer (Blue-Green)
# Switch traffic back to Blue environment
# (Immediate, zero downtime)

# 3. Rollback in Kubernetes
kubectl rollout undo deployment/examai-backend
kubectl rollout status deployment/examai-backend

# 4. Notify team
slack-notify "⚠️ Production rollback completed. Investigating issue."
```

### Scenario 2: Database Migration Issue

**Symptoms:**
- Migration failed
- Data corruption
- Schema mismatch

**Rollback Steps:**

```bash
# 1. DO NOT PANIC
# Database rollbacks are more complex

# 2. Check migration status
docker-compose run --rm backend alembic current

# 3. If migration partially completed:
# Option A: Rollback migration (if safe)
docker-compose run --rm backend alembic downgrade -1

# Option B: Restore from backup (if rollback not safe)
# Stop application first
docker-compose down

# Restore database
pg_restore -d examai_production /backups/backup_pre_migration_20251118.sql

# Restart application on previous version
git checkout v1.1.0
docker-compose up -d

# 4. Verify data integrity
docker-compose run --rm backend python scripts/verify_data.py
```

### Scenario 3: Third-Party Service Outage

**Example: Gemini API down**

```bash
# 1. Check service status
curl https://status.google.com/

# 2. Enable circuit breaker (if implemented)
redis-cli SET "circuit_breaker:gemini_api" "open"

# 3. Fallback options:
# - Queue requests for later processing
# - Use cached responses
# - Switch to backup AI model (GPT-4, Claude)

# 4. Notify users
# Show banner: "AI features temporarily limited"
```

---

## Security Considerations

### SSL/TLS Configuration

```nginx
# Production NGINX SSL config
server {
    listen 443 ssl http2;
    server_name app.examai.com;

    # SSL certificates (Let's Encrypt or CloudFlare)
    ssl_certificate /etc/letsencrypt/live/examai.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/examai.com/privkey.pem;

    # Strong SSL configuration
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers 'ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.examai.com;" always;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name app.examai.com;
    return 301 https://$server_name$request_uri;
}
```

### Firewall Rules

```bash
# UFW (Ubuntu)
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp    # SSH (restrict to office IP)
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Restrict SSH to specific IPs
ufw delete allow 22/tcp
ufw allow from 203.0.113.0/24 to any port 22
```

### Docker Security

```bash
# Run containers as non-root
USER appuser

# Read-only root filesystem
docker run --read-only ...

# Limit resources
docker run --memory="512m" --cpus="0.5" ...

# Security scanning
docker scan examai-backend:latest

# Trivy vulnerability scanner
trivy image examai-backend:latest
```

---

## Scaling Strategy

### Horizontal Scaling (Add more servers)

```bash
# AWS Auto Scaling Group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name examai-backend-asg \
  --launch-template LaunchTemplateName=examai-backend \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 3 \
  --target-group-arns arn:aws:elasticloadbalancing:... \
  --health-check-type ELB \
  --health-check-grace-period 300

# Scaling policies
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name examai-backend-asg \
  --policy-name scale-up \
  --scaling-adjustment 2 \
  --adjustment-type ChangeInCapacity \
  --cooldown 300
```

### Vertical Scaling (Bigger servers)

```bash
# Kubernetes: Increase resource limits
kubectl set resources deployment/examai-backend \
  --limits=cpu=2000m,memory=4Gi \
  --requests=cpu=1000m,memory=2Gi
```

### Database Scaling

```bash
# Read replicas for read-heavy workloads
# Primary: Write operations
# Replicas: Read operations

# Connection pooling (PgBouncer)
docker run -d --name pgbouncer \
  -e DB_USER=examai \
  -e DB_PASSWORD=xxx \
  -e DB_HOST=postgres-primary \
  -e POOL_MODE=transaction \
  -e MAX_CLIENT_CONN=1000 \
  -e DEFAULT_POOL_SIZE=25 \
  -p 6432:6432 \
  pgbouncer/pgbouncer
```

---

## Troubleshooting

### Common Issues

**1. Container won't start**

```bash
# Check logs
docker-compose logs backend

# Check resource usage
docker stats

# Inspect container
docker inspect examai_backend
```

**2. Database connection errors**

```bash
# Test connection
docker-compose run --rm backend python -c "from app.database import engine; print(engine.connect())"

# Check PostgreSQL logs
docker-compose logs postgres
```

**3. Out of memory**

```bash
# Check memory usage
free -h
docker stats

# Increase container limits
# Edit docker-compose.yml
services:
  backend:
    mem_limit: 2g
```

---

## Next Steps

1. ✅ Review deployment guide
2. ⬜ Set up CI/CD pipeline (GitHub Actions)
3. ⬜ Configure staging environment
4. ⬜ Set up monitoring (Grafana + Prometheus)
5. ⬜ Configure alerts (PagerDuty/Slack)
6. ⬜ Test rollback procedures
7. ⬜ Document runbooks for common incidents
8. ⬜ Schedule disaster recovery drill

---

## References

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PostgreSQL High Availability](https://www.postgresql.org/docs/current/high-availability.html)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [The Twelve-Factor App](https://12factor.net/)
