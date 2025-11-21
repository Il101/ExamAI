import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.db.session import AsyncSessionLocal

async def check_table():
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT to_regclass('public.subscriptions')"))
            exists = result.scalar() is not None
            print(f"Table 'subscriptions' exists: {exists}")
    except Exception as e:
        print(f"Error checking table: {e}")

if __name__ == "__main__":
    asyncio.run(check_table())
