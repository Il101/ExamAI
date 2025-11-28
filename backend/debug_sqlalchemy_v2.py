import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from sqlalchemy.engine.url import make_url

async def main():
    print("--- Debugging SQLAlchemy Connection V2 ---")
    db_url = os.getenv("DATABASE_URL")
    
    # Parse URL
    url_obj = make_url(db_url)
    
    # Method 1: Pass statement_cache_size in query params of URL
    print("\nAttempt 3: statement_cache_size in URL query")
    try:
        # Add statement_cache_size to query params
        query_params = dict(url_obj.query)
        query_params["statement_cache_size"] = "0"
        query_params["ssl"] = "require"
        
        # Reconstruct URL with new query params
        new_url = url_obj._replace(query=query_params).render_as_string(hide_password=False)
        print(f"URL with query: {new_url}")
        
        # Create engine WITHOUT connect_args (relying on URL)
        engine = create_async_engine(
            new_url,
            pool_pre_ping=True
        )
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ SQLAlchemy Connection Successful (URL Query)! Version: {version}")
        await engine.dispose()
    except Exception as e:
        print(f"❌ Attempt 3 Failed: {e}")

    # Method 2: Pass 'prepared_statement_cache_size' in connect_args (some docs suggest this for asyncpg via sqlalchemy?)
    # Actually asyncpg uses 'statement_cache_size'.
    # Let's try passing it as a string "0" in connect_args?
    
    print("\nAttempt 4: statement_cache_size='0' (string) in connect_args")
    try:
        clean_url = url_obj._replace(query={}).render_as_string(hide_password=False)
        connect_args = {
            "statement_cache_size": 0, # Int
            "ssl": "require"
        }
        # Maybe it needs to be nested? No, asyncpg takes kwargs.
        
        engine = create_async_engine(
            clean_url,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        # Force a new connection creation
        async with engine.connect() as conn:
             result = await conn.execute(text("SELECT version()"))
             print(f"✅ Attempt 4 Success")
    except Exception as e:
        print(f"❌ Attempt 4 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
