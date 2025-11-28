import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlalchemy.engine.url import make_url

async def main():
    print("--- Debugging SQLAlchemy Connection V4 ---")
    db_url = os.getenv("DATABASE_URL")
    
    # Parse URL and strip query params
    url_obj = make_url(db_url)
    clean_url = url_obj._replace(query={}).render_as_string(hide_password=False)
    print(f"Clean URL: {clean_url}")
    
    # Define name func to return None explicitly
    def name_func():
        return None

    # Pass ALL settings in connect_args
    connect_args = {
        "statement_cache_size": 0,          # For asyncpg
        "prepared_statement_cache_size": 0, # For SQLAlchemy dialect
        "prepared_statement_name_func": name_func, # Force unnamed
        "ssl": "require"
    }
    print(f"connect_args: {connect_args}")
    
    try:
        print("Attempt 6: Force name=None")
        engine = create_async_engine(
            clean_url,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ SQLAlchemy Connection Successful! Version: {version}")
        await engine.dispose()
        
    except Exception as e:
        print(f"❌ Attempt 6 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
