# Stage 10 Deployment - Installation Instructions

## 🚀 Quick Start

### 1. Install New Dependencies

```bash
cd backend
pip install python-json-logger>=2.0.7
# Or reinstall all:
pip install -r requirements.txt
```

### 2. Test Health Endpoints

```bash
# Start the application
uvicorn app.main:app --reload

# In another terminal, test endpoints:
curl http://localhost:8000/health
curl http://localhost:8000/health/detailed
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/live
```

Expected output for `/health`:
```json
{
  "status": "healthy",
  "service": "examai-backend",
  "environment": "development"
}
```

### 3. Test Docker Build

```bash
# Build production image
docker build -f backend/Dockerfile -t examai-backend:latest backend/

# Run with docker-compose
docker-compose -f docker-compose.prod.yml up
```

### 4. Run Deployment Checks

```bash
# Make scripts executable (already done)
chmod +x scripts/*.sh

# Run pre-deployment checks
./scripts/deploy-check.sh
```

## 📋 What's New in Stage 10

### New Files Created
- ✅ `app/core/monitoring.py` - Sentry integration
- ✅ `app/core/logging.py` - Structured JSON logging
- ✅ `app/api/v1/endpoints/health.py` - Health check endpoints
- ✅ `app/middleware/security.py` - Security headers + request logging
- ✅ `.env.production.example` - Production environment template
- ✅ `railway.toml` - Railway.app configuration
- ✅ `docker-compose.prod.yml` - Production orchestration
- ✅ `.github/workflows/test-and-deploy.yml` - CI/CD pipeline
- ✅ `scripts/migrate.sh` - Database migrations
- ✅ `scripts/deploy-check.sh` - Pre-deployment validation
- ✅ `scripts/backup-db.sh` - Database backup
- ✅ `scripts/restore-db.sh` - Database restore

### Modified Files
- ✏️ `app/main.py` - Added monitoring, logging, security middleware
- ✏️ `app/api/v1/router.py` - Added health endpoints
- ✏️ `requirements.txt` - Added python-json-logger

## 🔧 Configuration

### Environment Variables (Production)

Copy `.env.production.example` to `.env.production` and fill in:

```bash
cp .env.production.example .env.production
# Edit .env.production with your values
```

**Required variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - Generate with `openssl rand -hex 32`
- `GEMINI_API_KEY` - Google Gemini API key
- `SENTRY_DSN` - Sentry error tracking DSN (optional but recommended)

### GitHub Secrets

Configure these secrets in GitHub repository settings:

```
GEMINI_API_KEY
RAILWAY_TOKEN
RAILWAY_TOKEN_STAGING
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_ID
PRODUCTION_DATABASE_URL
CODECOV_TOKEN (optional)
SLACK_WEBHOOK (optional)
```

## 🧪 Testing

### Test Monitoring (Sentry)

```python
# Test error capture
from app.core.monitoring import capture_exception, capture_message

try:
    raise ValueError("Test error")
except Exception as e:
    capture_exception(e, context={"test": "value"})

capture_message("Test message", level="info")
```

### Test Logging

```python
from app.core.logging import get_logger, log_info, log_error

logger = get_logger(__name__)
log_info(logger, "User action", user_id="123", action="login")
log_error(logger, "Failed operation", error=ValueError("test"))
```

### Test Health Checks

```bash
# Basic health
curl http://localhost:8000/health

# Detailed (checks DB, Redis, Celery)
curl http://localhost:8000/health/detailed

# Kubernetes readiness
curl http://localhost:8000/health/ready

# Kubernetes liveness
curl http://localhost:8000/health/live
```

## 🚢 Deployment

### Option 1: Railway.app (Recommended)

1. Install Railway CLI:
```bash
npm install -g @railway/cli
```

2. Login and link project:
```bash
railway login
railway link
```

3. Set environment variables:
```bash
railway variables set DATABASE_URL="postgresql://..."
railway variables set REDIS_URL="redis://..."
# ... etc
```

4. Deploy:
```bash
railway up
```

### Option 2: Docker + Manual Deploy

1. Build image:
```bash
docker build -f backend/Dockerfile -t examai-backend:latest backend/
```

2. Push to registry:
```bash
docker tag examai-backend:latest your-registry/examai-backend:latest
docker push your-registry/examai-backend:latest
```

3. Deploy to your platform (AWS, GCP, Azure, etc.)

### Option 3: GitHub Actions (Automated)

Just push to `main` or `develop` branch:

```bash
git push origin main  # → Production deployment
git push origin develop  # → Staging deployment
```

## 📊 Monitoring

### Sentry Dashboard
- URL: https://sentry.io
- View errors, performance, user feedback

### Railway Logs
```bash
railway logs --service backend
railway logs --service celery-worker
```

### Health Monitoring
Set up uptime monitoring (e.g., UptimeRobot) for:
- `https://your-app.railway.app/health`

## 🔄 Maintenance

### Database Migrations
```bash
./scripts/migrate.sh
```

### Database Backup
```bash
./scripts/backup-db.sh
```

### Database Restore
```bash
./scripts/restore-db.sh backups/examai_backup_20251119_120000.sql.gz
```

### Pre-Deployment Check
```bash
./scripts/deploy-check.sh
```

## 🐛 Troubleshooting

### Import Error: pythonjsonlogger
```bash
pip install python-json-logger
```

### Health Check 503 Error
- Check DATABASE_URL is correct
- Ensure database is accessible
- Verify Redis is running

### Docker Build Fails
```bash
# Clear Docker cache
docker builder prune -a
docker-compose -f docker-compose.prod.yml build --no-cache
```

### Sentry Not Receiving Errors
- Check SENTRY_DSN is set
- Ensure ENVIRONMENT=production
- Test with `capture_message("test")`

## ✅ Verification Checklist

Before deploying to production:

- [ ] All tests pass (`pytest tests/`)
- [ ] Health endpoints respond (`/health`, `/health/detailed`)
- [ ] Docker builds successfully
- [ ] Environment variables configured
- [ ] Sentry receives test events
- [ ] Database migrations applied
- [ ] Backup script tested
- [ ] CI/CD pipeline runs successfully
- [ ] Monitoring dashboards accessible

## 📚 Additional Resources

- [Railway Documentation](https://docs.railway.app)
- [Sentry Documentation](https://docs.sentry.io)
- [Docker Documentation](https://docs.docker.com)
- [GitHub Actions](https://docs.github.com/en/actions)

---

**Status**: ✅ Stage 10 Complete  
**Date**: November 19, 2025
