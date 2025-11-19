#!/bin/bash
# Final deployment readiness check
# Run this before deploying to production

set -e

echo "🚀 ExamAI Pro - Deployment Readiness Check"
echo "=========================================="
echo ""

CHECKS_PASSED=0
CHECKS_FAILED=0
WARNINGS=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_pass() {
    echo -e "${GREEN}✅ $1${NC}"
    ((CHECKS_PASSED++))
}

check_fail() {
    echo -e "${RED}❌ $1${NC}"
    ((CHECKS_FAILED++))
}

check_warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    ((WARNINGS++))
}

# Change to backend directory
cd "$(dirname "$0")/../backend"

echo "${BLUE}1️⃣ Environment Configuration${NC}"
echo "----------------------------"

if [ -f .env ]; then
    check_pass ".env file exists"
    
    # Check required variables
    source .env 2>/dev/null || true
    
    if [ -n "$DATABASE_URL" ]; then
        check_pass "DATABASE_URL configured"
    else
        check_fail "DATABASE_URL not set"
    fi
    
    if [ -n "$REDIS_URL" ]; then
        check_pass "REDIS_URL configured"
    else
        check_fail "REDIS_URL not set"
    fi
    
    if [ -n "$SECRET_KEY" ]; then
        check_pass "SECRET_KEY configured"
    else
        check_fail "SECRET_KEY not set"
    fi
    
    if [ -n "$GEMINI_API_KEY" ]; then
        check_pass "GEMINI_API_KEY configured"
    else
        check_fail "GEMINI_API_KEY not set"
    fi
    
    if [ -n "$SENTRY_DSN" ]; then
        check_pass "Sentry monitoring configured"
    else
        check_warn "Sentry DSN not set (monitoring disabled)"
    fi
else
    check_fail ".env file not found"
fi

echo ""
echo "${BLUE}2️⃣ Dependencies${NC}"
echo "----------------------------"

if command -v python3 &> /dev/null; then
    check_pass "Python 3 installed"
    python_version=$(python3 --version)
    echo "   Version: $python_version"
else
    check_fail "Python 3 not found"
fi

if pip list 2>/dev/null | grep -q "fastapi"; then
    check_pass "FastAPI installed"
else
    check_fail "FastAPI not installed"
fi

if pip list 2>/dev/null | grep -q "python-json-logger"; then
    check_pass "python-json-logger installed (Stage 10 requirement)"
else
    check_fail "python-json-logger not installed - run: pip install python-json-logger"
fi

if pip list 2>/dev/null | grep -q "sentry-sdk"; then
    check_pass "Sentry SDK installed"
else
    check_warn "Sentry SDK not installed"
fi

echo ""
echo "${BLUE}3️⃣ Application${NC}"
echo "----------------------------"

if python3 -c "from app.main import app" 2>/dev/null; then
    check_pass "Application imports successfully"
else
    check_fail "Application import failed"
fi

if python3 -c "from app.core.monitoring import init_monitoring" 2>/dev/null; then
    check_pass "Monitoring module imports"
else
    check_fail "Monitoring module import failed"
fi

if python3 -c "from app.core.logging import setup_logging" 2>/dev/null; then
    check_pass "Logging module imports"
else
    check_fail "Logging module import failed"
fi

if python3 -c "from app.api.v1.endpoints.health import router" 2>/dev/null; then
    check_pass "Health endpoints available"
else
    check_fail "Health endpoints import failed"
fi

echo ""
echo "${BLUE}4️⃣ Database${NC}"
echo "----------------------------"

if [ -f "alembic.ini" ]; then
    check_pass "Alembic configuration exists"
else
    check_fail "alembic.ini not found"
fi

if [ -d "alembic/versions" ] && [ "$(ls -A alembic/versions/*.py 2>/dev/null | wc -l)" -gt 0 ]; then
    migration_count=$(ls -1 alembic/versions/*.py 2>/dev/null | wc -l)
    check_pass "Database migrations exist ($migration_count migration files)"
else
    check_warn "No migration files found"
fi

echo ""
echo "${BLUE}5️⃣ Testing${NC}"
echo "----------------------------"

if [ -d "tests" ]; then
    test_count=$(find tests -name "test_*.py" | wc -l)
    check_pass "Test suite exists ($test_count test files)"
else
    check_warn "No tests directory found"
fi

if [ -f "pytest.ini" ]; then
    check_pass "pytest configuration exists"
else
    check_warn "pytest.ini not found"
fi

echo ""
echo "${BLUE}6️⃣ Docker${NC}"
echo "----------------------------"

if [ -f "Dockerfile" ]; then
    check_pass "Dockerfile exists"
else
    check_fail "Dockerfile not found"
fi

if [ -f "../docker-compose.yml" ]; then
    check_pass "docker-compose.yml exists"
else
    check_warn "docker-compose.yml not found"
fi

if [ -f "../docker-compose.prod.yml" ]; then
    check_pass "docker-compose.prod.yml exists (Stage 10)"
else
    check_fail "docker-compose.prod.yml not found"
fi

echo ""
echo "${BLUE}7️⃣ CI/CD${NC}"
echo "----------------------------"

if [ -f "../.github/workflows/test-and-deploy.yml" ]; then
    check_pass "GitHub Actions workflow exists"
else
    check_fail "CI/CD workflow not found"
fi

echo ""
echo "${BLUE}8️⃣ Documentation${NC}"
echo "----------------------------"

if [ -f "../README.md" ]; then
    check_pass "README.md exists"
else
    check_warn "README.md not found"
fi

if [ -f "../PROJECT_SUMMARY.md" ]; then
    check_pass "PROJECT_SUMMARY.md exists"
else
    check_warn "PROJECT_SUMMARY.md not found"
fi

if [ -f "../docs/STAGE_10_STATUS.md" ]; then
    check_pass "Stage 10 documentation exists"
else
    check_warn "Stage 10 docs not found"
fi

echo ""
echo "${BLUE}9️⃣ Deployment Scripts${NC}"
echo "----------------------------"

if [ -f "../scripts/migrate.sh" ] && [ -x "../scripts/migrate.sh" ]; then
    check_pass "migrate.sh exists and is executable"
else
    check_warn "migrate.sh not found or not executable"
fi

if [ -f "../scripts/backup-db.sh" ] && [ -x "../scripts/backup-db.sh" ]; then
    check_pass "backup-db.sh exists and is executable"
else
    check_warn "backup-db.sh not found or not executable"
fi

if [ -f "../scripts/deploy-check.sh" ] && [ -x "../scripts/deploy-check.sh" ]; then
    check_pass "deploy-check.sh exists and is executable"
else
    check_warn "deploy-check.sh not found or not executable"
fi

echo ""
echo "=========================================="
echo "${BLUE}📊 Summary${NC}"
echo "=========================================="
echo -e "Checks passed:  ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks failed:  ${RED}$CHECKS_FAILED${NC}"
echo -e "Warnings:       ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All critical checks passed!${NC}"
    echo ""
    echo "🚀 Ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "  1. Run tests: pytest tests/ -v"
    echo "  2. Build Docker: docker-compose -f docker-compose.prod.yml build"
    echo "  3. Configure production environment in .env.production"
    echo "  4. Set up GitHub Secrets for CI/CD"
    echo "  5. Deploy: git push origin main"
    echo ""
    exit 0
else
    echo -e "${RED}❌ $CHECKS_FAILED critical check(s) failed${NC}"
    echo ""
    echo "Please fix the issues above before deploying."
    echo ""
    exit 1
fi
