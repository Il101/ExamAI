import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from google import genai
from supabase import create_client
from jose import jwt

# Load environment variables
load_dotenv()

async def check_database():
    print("\n--- Checking Database ---")
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not found in .env")
        return False
    
    is_local = "localhost" in db_url or "127.0.0.1" in db_url
    print(f"Target: {'Localhost' if is_local else 'Remote (Supabase)'}")
    print(f"Connecting to: {db_url.split('@')[-1]}") # Hide credentials
    
    # Determine connection args (e.g. SSL for Supabase)
    # Force disable prepared statements for Supabase/PgBouncer
    connect_args = {
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: "",
    }
    
    if "supabase.com" in db_url:
        connect_args["ssl"] = "require"

    print(f"DEBUG: connect_args={connect_args}")

    # Parse and clean URL to remove conflicting query parameters
    try:
        from sqlalchemy.engine.url import make_url
        url_obj = make_url(db_url)
        if url_obj.query:
            print(f"DEBUG: Stripping query params from URL: {url_obj.query}")
            db_url = url_obj._replace(query={}).render_as_string(hide_password=False)
    except Exception as e:
        print(f"WARNING: Failed to parse/clean URL: {e}")

    try:
        engine = create_async_engine(db_url, connect_args=connect_args)
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def check_supabase_auth():
    print("\n--- Checking Supabase Auth & JWT Secret ---")
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    secret = os.getenv("SECRET_KEY")
    
    if not all([url, key, secret]):
        print("❌ Missing Supabase credentials in .env")
        return False

    try:
        supabase = create_client(url, key)
        # Try to sign in with a non-existent user to check API connectivity
        # We expect "Invalid login credentials" or similar, which means API is reachable
        try:
            supabase.auth.sign_in_with_password({"email": "check_setup@example.com", "password": "wrong_password"})
        except Exception as e:
            if "Invalid login credentials" in str(e) or "Email not confirmed" in str(e):
                print("✅ Supabase API is reachable (Credentials valid)")
            else:
                # If we can't verify via login failure, we can't easily verify the JWT secret 
                # without a real token. But we can verify the secret format.
                print(f"⚠️  Supabase API response: {str(e)}")
        
        # Verify Secret Key format (simple check)
        if len(secret) > 32:
             print("✅ JWT Secret Key present and looks valid (length > 32)")
             return True
        else:
             print("❌ JWT Secret Key looks too short")
             return False
             
    except Exception as e:
        print(f"❌ Supabase connection failed: {str(e)}")
        return False

def check_gemini():
    print("\n--- Checking Gemini API ---")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found in .env")
        return False
        
    try:
        # Use new SDK client API
        client = genai.Client(api_key=api_key)
        # Use model from env or fallback
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        print(f"Testing model: {model_name}")
        
        response = client.models.generate_content(
            model=model_name,
            contents="Say 'OK'"
        )
        
        if response and response.text:
            print(f"✅ Gemini API successful. Response: {response.text.strip()}")
            return True
        else:
            print("❌ Gemini API returned empty response")
            return False
    except Exception as e:
        print(f"❌ Gemini API failed: {str(e)}")
        return False

async def main():
    print("Starting Environment Verification...")
    
    db_ok = await check_database()
    supa_ok = check_supabase_auth()
    gemini_ok = check_gemini()
    
    if db_ok and supa_ok and gemini_ok:
        print("\n✅✅✅ ALL SYSTEMS GO! Ready for Stage 10. ✅✅✅")
        sys.exit(0)
    else:
        print("\n❌❌❌ Verification Failed. Please check your .env file. ❌❌❌")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
