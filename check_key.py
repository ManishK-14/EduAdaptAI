from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv("GEMINI_API_KEY", "")
print(f"Key length: {len(key)}")
print(f"Starts with AIza: {key.startswith('AIza')}")
print(f"Is placeholder: {key == 'your_gemini_api_key_here'}")
print(f"Key preview: {key[:8]}...{key[-4:]}" if len(key) > 12 else f"Key: {key}")
