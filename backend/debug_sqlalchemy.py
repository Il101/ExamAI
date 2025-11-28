import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlalchemy.engine.url import make_url

async def main():
    print("--- Debugging SQLAlchemy Connection ---")
    db_url = os.getenv("DATABASE_URL")
    
    # Parse URL and strip query params
    url_obj = make_url(db_url)
    clean_url = url_obj._replace(query={}).render_as_string(hide_password=False)
    print(f"Clean URL: {clean_url}")
    
    connect_args = {
        "statement_cache_size": 0,
        "ssl": "require"
    }
    print(f"connect_args: {connect_args}")
    
    try:
        # Try with pool_pre_ping=True first (as in app)
        print("Attempt 1: pool_pre_ping=True")
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
        print(f"❌ Attempt 1 Failed: {e}")
        
        try:
            # Try with pool_pre_ping=False
            print("\nAttempt 2: pool_pre_ping=False")
            engine = create_async_engine(
                clean_url,
                connect_args=connect_args,
                pool_pre_ping=False
            )
            async with engine.connect() as conn:
                result = await conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"✅ SQLAlchemy Connection Successful (No Pre-Ping)! Version: {version}")
            await engine.dispose()
        except Exception as e2:
            print(f"❌ Attempt 2 Failed: {e2}")

if __name__ == "__main__":
    asyncio.run(main())
