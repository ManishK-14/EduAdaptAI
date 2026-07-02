"""Full end-to-end test with the correct model."""
from dotenv import load_dotenv
import os, warnings, time
load_dotenv()
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.0-flash"

# Test 1: Basic text
print("=" * 50)
print("TEST 1: Basic text generation")
try:
    model = genai.GenerativeModel(MODEL)
    resp = model.generate_content("Say exactly: 'Gemini is working!'")
    print(f"  ✅ {resp.text.strip()}")
except Exception as e:
    print(f"  ❌ {type(e).__name__}: {e}")

# Test 2: PDF File API upload
print("\n" + "=" * 50)
print("TEST 2: PDF File API upload + Vision")
pdf_path = "data/uploads/ved ant notes .pdf"
if not os.path.exists(pdf_path):
    print(f"  ⚠️ PDF not found at {pdf_path}")
else:
    try:
        print(f"  Uploading {pdf_path}...")
        uploaded = genai.upload_file(path=pdf_path, mime_type="application/pdf")
        print(f"  Upload state: {uploaded.state.name}")

        while uploaded.state.name == "PROCESSING":
            print("  ⏳ Waiting for Gemini to process the file...")
            time.sleep(3)
            uploaded = genai.get_file(uploaded.name)

        print(f"  Final state: {uploaded.state.name}")

        if uploaded.state.name == "ACTIVE":
            model = genai.GenerativeModel(MODEL)
            resp = model.generate_content([
                "What subject is this document about? Answer in one sentence.",
                uploaded
            ])
            print(f"  ✅ Gemini read the PDF: {resp.text.strip()}")
        else:
            print(f"  ❌ File processing failed with state: {uploaded.state.name}")

        # Cleanup
        genai.delete_file(uploaded.name)
        print("  🗑️ Cleaned up")

    except Exception as e:
        print(f"  ❌ {type(e).__name__}: {e}")

print("\n" + "=" * 50)
print("ALL TESTS COMPLETE")
