
try:
    from google.genai import types
    print("Available attributes in google.genai.types:")
    for attr in dir(types):
        if "Retry" in attr or "Http" in attr:
            print(f"- {attr}")
            
    # Check HttpOptions fields if possible
    if hasattr(types, "HttpOptions"):
        from pydantic import BaseModel
        if issubclass(types.HttpOptions, BaseModel):
            print("\nHttpOptions fields:")
            print(types.HttpOptions.model_fields.keys())
        elif hasattr(types.HttpOptions, "__annotations__"):
            print("\nHttpOptions annotations:")
            print(types.HttpOptions.__annotations__)
            
except ImportError:
    print("Could not import google.genai.types")
except Exception as e:
    print(f"Error: {e}")
