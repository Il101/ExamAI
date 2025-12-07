import asyncio
import asyncpg
import os

async def main():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL not set")
        return
    
    # Convert asyncpg URL format
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(database_url)
    
    # Delete the migration record
    await conn.execute("DELETE FROM alembic_version WHERE version_num = '1234567890ab'")
    
    # Verify
    result = await conn.fetch("SELECT * FROM alembic_version")
    print("Current alembic versions:", result)
    
    await conn.close()
    print("Migration record deleted successfully!")

if __name__ == "__main__":
    asyncio.run(main())
