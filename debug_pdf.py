"""Diagnostic script to test each PDF extraction strategy."""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

PDF_PATH = Path("data/uploads/ved ant notes .pdf")
print(f"File exists: {PDF_PATH.exists()}")
print(f"File size: {PDF_PATH.stat().st_size:,} bytes")
print()

# Strategy 1: pdfplumber
print("=" * 50)
print("STRATEGY 1: pdfplumber")
try:
    import pdfplumber
    with pdfplumber.open(PDF_PATH) as pdf:
        print(f"  Pages: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages[:3]):
            text = page.extract_text()
            if text and text.strip():
                print(f"  Page {i+1}: {len(text)} chars -> {text[:100]}...")
            else:
                print(f"  Page {i+1}: NO TEXT")
except Exception as e:
    print(f"  ERROR: {e}")

# Strategy 2: pypdfium2
print("\n" + "=" * 50)
print("STRATEGY 2: pypdfium2")
try:
    import pypdfium2 as pdfium
    pdf = pdfium.PdfDocument(str(PDF_PATH))
    print(f"  Pages: {len(pdf)}")
    for i in range(min(len(pdf), 3)):
        page = pdf[i]
        textpage = page.get_textpage()
        text = textpage.get_text_range()
        if text and text.strip():
            print(f"  Page {i+1}: {len(text)} chars -> {text[:100]}...")
        else:
            print(f"  Page {i+1}: NO TEXT")
        textpage.close()
        page.close()
    pdf.close()
except Exception as e:
    print(f"  ERROR: {e}")

# Strategy 3: PyMuPDF
print("\n" + "=" * 50)
print("STRATEGY 3: PyMuPDF text")
try:
    import fitz
    doc = fitz.open(str(PDF_PATH))
    print(f"  Pages: {len(doc)}")
    for i, page in enumerate(doc[:3]):
        text = page.get_text("text")
        if text and text.strip():
            print(f"  Page {i+1}: {len(text)} chars -> {text[:100]}...")
        else:
            print(f"  Page {i+1}: NO TEXT")
    doc.close()
except Exception as e:
    print(f"  ERROR: {e}")

# Strategy 4: PyMuPDF image rendering
print("\n" + "=" * 50)
print("STRATEGY 4: PyMuPDF -> image rendering")
try:
    import fitz
    from PIL import Image
    import io
    doc = fitz.open(str(PDF_PATH))
    page = doc[0]
    pix = page.get_pixmap(dpi=200)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    print(f"  Page 1 rendered: {img.size} pixels, mode={img.mode}")
    doc.close()
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Strategy 5: Gemini Vision OCR
print("\n" + "=" * 50)
print("STRATEGY 5: Gemini Vision OCR")
api_key = os.getenv("GEMINI_API_KEY")
print(api_key)
print(f"  API key present: {bool(api_key and api_key != 'your_gemini_api_key_here')}")
print(f"  API key prefix: {api_key[:12]}..." if api_key else "  No key")

try:
    import fitz
    from PIL import Image
    import io
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    doc = fitz.open(str(PDF_PATH))
    page = doc[0]
    pix = page.get_pixmap(dpi=200)
    img_bytes = pix.tobytes("png")
    img = Image.open(io.BytesIO(img_bytes))
    doc.close()

    print("  Sending page 1 image to Gemini...")
    response = model.generate_content([
        "Extract ALL the text from this image exactly as written. Return ONLY the text.",
        img
    ])
    if response and response.text:
        print(f"  SUCCESS: {len(response.text)} chars extracted")
        print(f"  Preview: {response.text[:200]}...")
    else:
        print(f"  EMPTY RESPONSE")
        if response:
            print(f"  Prompt feedback: {response.prompt_feedback}")
            for c in response.candidates:
                print(f"  Candidate finish reason: {c.finish_reason}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
