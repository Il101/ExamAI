import google.generativeai as genai
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def test_simple():
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    print(f"Testing API key: {api_key[:20]}...")
    print(f"Model: {model_name}")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(model_name)
    
    try:
        print("Calling Gemini API...")
        response = await model.generate_content_async("Say hello in one word")
        print(f"Success! Response: {response.text}")
        print(f"Tokens: {response.usage_metadata.prompt_token_count}/{response.usage_metadata.candidates_token_count}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_simple())
