"""
Quick script to check recent failed exams and their error messages.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.db.session import AsyncSessionLocal
from sqlalchemy import select, desc
from app.db.models.exam import ExamModel


async def check_failed_exams():
    """Check recent failed exams."""
    async with AsyncSessionLocal() as session:
        # Query recent failed exams
        stmt = (
            select(ExamModel)
            .where(ExamModel.status == "failed")
            .order_by(desc(ExamModel.created_at))
            .limit(10)
        )
        
        result = await session.execute(stmt)
        exams = result.scalars().all()
        
        if not exams:
            print("✅ No failed exams found")
            return
        
        print(f"❌ Found {len(exams)} failed exams:\n")
        
        for exam in exams:
            print(f"Exam ID: {exam.id}")
            print(f"  Title: {exam.title}")
            print(f"  Subject: {exam.subject}")
            print(f"  Created: {exam.created_at}")
            print(f"  Failed: {exam.failed_at if hasattr(exam, 'failed_at') else 'N/A'}")
            
            # Check for error fields
            if hasattr(exam, 'error_message'):
                print(f"  Error Message: {exam.error_message}")
            if hasattr(exam, 'error_category'):
                print(f"  Error Category: {exam.error_category}")
            
            print()


if __name__ == "__main__":
    asyncio.run(check_failed_exams())
