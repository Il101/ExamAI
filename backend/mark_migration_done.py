import asyncio
import asyncpg
import os

async def mark_migration_as_done():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        database_url = "postgresql://postgres.pjgtzblqhtpdtojgbzpe:JGUf3TEEcLf45GBg@aws-1-eu-west-2.pooler.supabase.com:6543/postgres"
    
    # Convert asyncpg URL format
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(database_url)
    
    try:
        # Check current version
        current = await conn.fetchval("SELECT version_num FROM alembic_version")
        print(f"Current migration: {current}")
        
        # Update to new migration
        await conn.execute(
            "UPDATE alembic_version SET version_num = 'b8f36f9d8bdf' WHERE version_num = '0815fa30ada3'"
        )
        
        # Verify
        new_version = await conn.fetchval("SELECT version_num FROM alembic_version")
        print(f"Updated to: {new_version}")
        
        # Now add the columns if they don't exist
        await conn.execute("""
            ALTER TABLE exams 
            ADD COLUMN IF NOT EXISTS original_file_url VARCHAR
        """)
        
        await conn.execute("""
            ALTER TABLE exams 
            ADD COLUMN IF NOT EXISTS original_file_mime_type VARCHAR
        """)
        
        await conn.execute("""
            ALTER TABLE topics 
            ADD COLUMN IF NOT EXISTS media_references TEXT
        """)
        
        print("✅ Columns added successfully")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(mark_migration_as_done())
