from dotenv import load_dotenv
import os, warnings
load_dotenv()
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Available models with generateContent:")
for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(f"  {m.name}")
