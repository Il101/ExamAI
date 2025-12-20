try:
    from pywebpush import vapid
    
    private_key_info = vapid.Vapid.from_string(None)
    
    print("\n--- VAPID KEYS GENERATED ---")
    print(f"VAPID_PRIVATE_KEY={private_key_info.private_key}")
    print(f"VAPID_PUBLIC_KEY={private_key_info.public_key}")
    print("\nNEXT_PUBLIC_VAPID_PUBLIC_KEY=" + private_key_info.public_key)
    print("----------------------------\n")
    print("Add these to your .env files (Backend for private/public, Frontend for public).")

except ImportError:
    print("pywebpush is not installed. Run: pip install pywebpush")
except Exception as e:
    print(f"An error occurred: {e}")
