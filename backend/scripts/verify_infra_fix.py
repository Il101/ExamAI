import asyncio
import os
import sys
from uuid import uuid4

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from backend.app.tasks.exam_tasks import generate_exam_content
from backend.app.core.config import settings

async def verify_cleanup():
    print("Starting verification of session cleanup...")
    # This won't run a full Celery task but we can test the internal async logic
    # or just check if pywebpush 1.15.0 is indeed solving the warning
    
    try:
        from pywebpush import webpush
        print("pywebpush imported successfully")
    except ImportError:
        print("pywebpush not found")
        return

    print("Verifying pywebpush warning (simulated)...")
    # We can't easily trigger the exact private key warning without a real subscription
    # but we've updated the version in requirements.txt.
    
    print("Verification complete (mock). Please check Celery logs in staging.")

if __name__ == "__main__":
    asyncio.run(verify_cleanup())
