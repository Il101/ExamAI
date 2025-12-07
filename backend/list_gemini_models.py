import os
from google import genai

# Get API key from environment
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not set in environment")
    exit(1)

# Create client
client = genai.Client(api_key=api_key)

# List all available models
print("Available Gemini models:\n")
print("-" * 80)

models = client.models.list()
for model in models:
    print(f"Name: {model.name}")
    print(f"  Display Name: {model.display_name}")
    print(f"  Description: {model.description}")
    
    # Check supported methods
    if hasattr(model, 'supported_generation_methods'):
        methods = model.supported_generation_methods
        print(f"  Supported Methods: {', '.join(methods)}")
    
    print("-" * 80)
