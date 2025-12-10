#!/bin/bash
# Toggle between old and new content generation architecture

CURRENT=$(grep "USE_UNIFIED_GENERATION" .env 2>/dev/null | cut -d'=' -f2)

if [ "$1" == "new" ]; then
    echo "🚀 Switching to NEW unified architecture..."
    if grep -q "USE_UNIFIED_GENERATION" .env 2>/dev/null; then
        sed -i '' 's/USE_UNIFIED_GENERATION=.*/USE_UNIFIED_GENERATION=true/' .env
    else
        echo "USE_UNIFIED_GENERATION=true" >> .env
    fi
    echo "✅ NEW architecture enabled"
    echo "   Restart backend: docker-compose restart backend celery"
    
elif [ "$1" == "old" ]; then
    echo "⏮️  Switching to OLD legacy architecture..."
    if grep -q "USE_UNIFIED_GENERATION" .env 2>/dev/null; then
        sed -i '' 's/USE_UNIFIED_GENERATION=.*/USE_UNIFIED_GENERATION=false/' .env
    else
        echo "USE_UNIFIED_GENERATION=false" >> .env
    fi
    echo "✅ OLD architecture enabled"
    echo "   Restart backend: docker-compose restart backend celery"
    
elif [ "$1" == "status" ]; then
    if [ "$CURRENT" == "true" ]; then
        echo "📊 Current: NEW unified architecture ✨"
    else
        echo "📊 Current: OLD legacy architecture 🔧"
    fi
    
else
    echo "Usage: ./toggle_generation.sh [new|old|status]"
    echo ""
    echo "Commands:"
    echo "  new     - Enable NEW unified architecture"
    echo "  old     - Enable OLD legacy architecture (fallback)"
    echo "  status  - Show current architecture"
    echo ""
    if [ "$CURRENT" == "true" ]; then
        echo "Current: NEW unified architecture ✨"
    else
        echo "Current: OLD legacy architecture 🔧"
    fi
fi
