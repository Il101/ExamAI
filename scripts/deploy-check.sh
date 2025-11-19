#!/bin/bash
# Pre-deployment check script
# Validates that all requirements are met before deploying

set -e

echo "🔍 Running pre-deployment checks..."

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to print check result
check_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((CHECKS_FAILED++))
    fi
}

# Check 1: All tests passing
echo ""
echo "1️⃣ Checking tests..."
cd backend
if pytest tests/ -q --tb=no; then
    check_result 0 "All tests passing"
else
    check_result 1 "Tests are failing"
fi

# Check 2: No pending migrations
echo ""
echo "2️⃣ Checking database migrations..."
if alembic check 2>&1 | grep -q "Target database is up to date"; then
    check_result 0 "No pending migrations"
else
    check_result 1 "Pending migrations found - run 'alembic upgrade head'"
fi

# Check 3: Environment variables
echo ""
echo "3️⃣ Checking environment variables..."
required_vars=("DATABASE_URL" "REDIS_URL" "SECRET_KEY" "GEMINI_API_KEY")
all_vars_set=true

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${YELLOW}⚠️  $var not set${NC}"
        all_vars_set=false
    fi
done

if $all_vars_set; then
    check_result 0 "All required environment variables set"
else
    check_result 1 "Missing required environment variables"
fi

# Check 4: Dependencies up to date
echo ""
echo "4️⃣ Checking dependencies..."
if pip list --outdated | grep -q "google-generativeai\|fastapi\|sqlalchemy"; then
    check_result 1 "Critical dependencies have updates available"
else
    check_result 0 "Dependencies are up to date"
fi

# Check 5: Code quality
echo ""
echo "5️⃣ Checking code quality..."
if black --check app tests > /dev/null 2>&1 && isort --check-only app tests > /dev/null 2>&1; then
    check_result 0 "Code formatting is correct"
else
    check_result 1 "Code formatting issues found - run 'black app tests && isort app tests'"
fi

# Check 6: Security vulnerabilities
echo ""
echo "6️⃣ Checking for security vulnerabilities..."
if pip-audit --desc > /dev/null 2>&1; then
    check_result 0 "No known security vulnerabilities"
else
    check_result 1 "Security vulnerabilities found - check pip-audit output"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Checks passed: ${GREEN}$CHECKS_PASSED${NC}"
echo -e "Checks failed: ${RED}$CHECKS_FAILED${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All pre-deployment checks passed. Ready to deploy!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please fix the issues before deploying.${NC}"
    exit 1
fi
