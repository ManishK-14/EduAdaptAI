"""
File processing module.
Handles PDF text extraction and raw text input processing.

Uses multiple text extraction strategies. If all fail (scanned PDF),
returns the file path so the app can use Gemini multimodal instead.
"""

import pdfplumber
import pypdfium2 as pdfium
from pathlib import Path
from typing import Optional
from utils.helpers import truncate_text, ensure_directory


MAX_FILE_SIZE_MB = 20
UPLOAD_DIR = Path("data/uploads")


def save_uploaded_file(uploaded_file) -> Path:
    """Save an uploaded Streamlit file to the uploads directory."""
    ensure_directory(UPLOAD_DIR)
    file_path = UPLOAD_DIR / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


# ── Text extraction strategies ──────────────────────────────────

def _extract_with_pdfplumber(file_path: Path) -> Optional[str]:
    try:
        all_text: list[str] = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    all_text.append(f"--- Page {page_num} ---\n{page_text}")
        if all_text:
            return "\n\n".join(all_text)
    except Exception:
        pass
    return None


def _extract_with_pypdfium2(file_path: Path) -> Optional[str]:
    try:
        all_text: list[str] = []
        pdf = pdfium.PdfDocument(str(file_path))
        for page_num in range(len(pdf)):
            page = pdf[page_num]
            textpage = page.get_textpage()
            page_text = textpage.get_text_range()
            if page_text and page_text.strip():
                all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
            textpage.close()
            page.close()
        pdf.close()
        if all_text:
            return "\n\n".join(all_text)
    except Exception:
        pass
    return None


def _extract_with_pymupdf(file_path: Path) -> Optional[str]:
    try:
        import fitz
    except ImportError:
        return None
    try:
        all_text: list[str] = []
        doc = fitz.open(str(file_path))
        for page_num, page in enumerate(doc, start=1):
            page_text = page.get_text("text")
            if page_text and page_text.strip():
                all_text.append(f"--- Page {page_num} ---\n{page_text}")
        doc.close()
        if all_text:
            return "\n\n".join(all_text)
    except Exception:
        pass
    return None


def extract_text_from_pdf(file_path: Path) -> Optional[str]:
    """Try all strategies. Returns extracted text or None."""
    for extractor in [_extract_with_pdfplumber, _extract_with_pypdfium2, _extract_with_pymupdf]:
        text = extractor(file_path)
        if text and len(text.strip()) > 20:
            return truncate_text(text)
    return None


# ── Main entry points ───────────────────────────────────────────

def process_text_input(raw_text: str) -> Optional[str]:
    """Clean and validate raw text input."""
    text = raw_text.strip()
    if not text or len(text) < 20:
        return None
    return truncate_text(text)


def process_uploaded_file(uploaded_file) -> tuple[Optional[str], Path]:
    """
    Process an uploaded file. Returns (extracted_text, file_path).
    
    - If text extraction succeeds: (text, file_path)
    - If PDF is scanned/image-based: (None, file_path) — caller should use multimodal
    
    Raises ValueError for unsupported formats or invalid files.
    """
    filename = uploaded_file.name.lower()

    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"File too large ({file_size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB.")

    file_path = save_uploaded_file(uploaded_file)

    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
        return (text, file_path)  # text may be None for scanned PDFs

    elif filename.endswith(".txt"):
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        processed = process_text_input(content)
        if not processed:
            raise ValueError("The text file appears to be empty or too short.")
        return (processed, file_path)

    else:
        raise ValueError(
            f"Unsupported file format: '{filename.split('.')[-1]}'. "
            "Please upload a PDF or TXT file."
        )
