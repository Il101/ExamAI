import asyncio
import os
import asyncpg
from sqlalchemy.engine.url import make_url

async def main():
    print("--- Debugging AsyncPG Connection ---")
    db_url = os.getenv("DATABASE_URL")
    print(f"Original URL: {db_url}")
    
    # Parse URL
    url = make_url(db_url)
    # Strip query params
    clean_url = url._replace(query={}).render_as_string(hide_password=False)
    print(f"Clean URL: {clean_url}")
    
    # Extract components for asyncpg
    user = url.username
    password = url.password
    host = url.host
    port = url.port
    database = url.database
    
    print(f"Connecting to {host}:{port}/{database} as {user}")
    
    # Test 1: statement_cache_size=100 (Should FAIL)
    print("\n--- Test 1: statement_cache_size=100 ---")
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            ssl="require",
            statement_cache_size=100
        )
        print("✅ Connection Successful")
        print("Executing query 1...")
        await conn.fetchval("SELECT version()")
        print("Executing query 2...")
        await conn.fetchval("SELECT version()")
        print("✅ Test 1 Passed (Unexpected!)")
        await conn.close()
    except Exception as e:
        print(f"❌ Test 1 Failed (Expected): {e}")

    # Test 2: statement_cache_size=0 (Should PASS)
    print("\n--- Test 2: statement_cache_size=0 ---")
    try:
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database,
            ssl="require",
            statement_cache_size=0
        )
        print("✅ Connection Successful")
        print("Executing query 1...")
        await conn.fetchval("SELECT version()")
        print("Executing query 2...")
        await conn.fetchval("SELECT version()")
        print("Executing fetchrow(';')...")
        await conn.fetchrow(";")
        
        print("Executing fetchrow(';') inside transaction...")
        async with conn.transaction():
            await conn.fetchrow(";")
            
        print("✅ Test 2 Passed (Success!)")
        await conn.close()
    except Exception as e:
        print(f"❌ Test 2 Failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
