#!/bin/bash
# Quick deployment preparation script
# Run this before deploying to production

set -e

echo "🚀 ExamAI Pro - Pre-Deployment Preparation"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Python dependencies
echo "1️⃣ Checking Python dependencies..."
cd backend
if pip show python-json-logger > /dev/null 2>&1; then
    echo -e "${GREEN}✅ python-json-logger installed${NC}"
else
    echo -e "${YELLOW}⚠️  Installing python-json-logger...${NC}"
    pip install "python-json-logger>=2.0.7"
fi

# Step 2: Test imports
echo ""
echo "2️⃣ Testing application imports..."
if python3 -c "from app.main import app; from app.core.monitoring import init_monitoring; from app.core.logging import setup_logging" 2>/dev/null; then
    echo -e "${GREEN}✅ All modules import successfully${NC}"
else
    echo -e "${RED}❌ Import errors detected${NC}"
    exit 1
fi

# Step 3: Run unit tests
echo ""
echo "3️⃣ Running unit tests..."
if pytest tests/unit/ -q --tb=no; then
    echo -e "${GREEN}✅ Unit tests passed${NC}"
else
    echo -e "${RED}❌ Unit tests failed${NC}"
    exit 1
fi

# Step 4: Check environment file
echo ""
echo "4️⃣ Checking environment configuration..."
if [ -f .env ]; then
    echo -e "${GREEN}✅ .env file exists${NC}"
else
    echo -e "${YELLOW}⚠️  .env file not found. Copy from .env.example${NC}"
fi

# Step 5: Check git status
echo ""
echo "5️⃣ Checking git status..."
cd ..
if [ -z "$(git status --porcelain)" ]; then
    echo -e "${GREEN}✅ Working directory clean${NC}"
else
    echo -e "${YELLOW}⚠️  Uncommitted changes detected${NC}"
    echo "Modified files:"
    git status --short | head -10
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✅ Pre-deployment preparation complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Review changes: git status"
echo "2. Commit changes: git add . && git commit -m 'Stage 10: Production deployment ready'"
echo "3. Push to GitHub: git push origin main"
echo "4. Configure GitHub Secrets for CI/CD"
echo "5. Deploy to Railway + Vercel"
echo ""
echo "For full checklist, see: docs/STAGE_10_STATUS.md"
