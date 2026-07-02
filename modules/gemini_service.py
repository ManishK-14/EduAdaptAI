"""
Gemini AI service module.
Handles all communication with the Google Gemini API.

Supports:
  1. process_lesson_content(text)     — for text-based lessons
  2. process_lesson_from_pdf(path)    — for scanned/image PDFs (uses File API upload)
  3. process_lesson_from_video(path)  — for MP4/MOV (File API upload + video prompt)
"""

import os
import time
import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", FutureWarning)
    import google.generativeai as genai
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from utils.prompts import LESSON_PROCESSING_PROMPT, PDF_PROCESSING_PROMPT, VIDEO_PROCESSING_PROMPT
from modules.video_processor import upload_video_and_wait_active
from utils.helpers import safe_parse_json, validate_lesson_data

# Load environment variables
load_dotenv()

# Model fallback chain — each model has its own separate free-tier quota
MODEL_NAMES = [
    "gemini-2.0-flash",
    "gemini-2.5-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-flash-lite-latest",
]
MAX_RETRIES = 2


def _configure_api() -> None:
    """Configure the Gemini API with the key from environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "" or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key not configured. "
            "Please set GEMINI_API_KEY in your .env file.\n"
            "Get a key at: https://aistudio.google.com/apikey"
        )
    genai.configure(api_key=api_key)


def _create_model(model_name: str | None = None) -> genai.GenerativeModel:
    """Create and return a configured Gemini GenerativeModel instance."""
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
    }

    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    return genai.GenerativeModel(
        model_name=model_name or MODEL_NAMES[0],
        generation_config=generation_config,
        safety_settings=safety_settings,
    )


def _parse_and_validate(raw_text: str, attempt: int) -> tuple[Optional[dict], Optional[str]]:
    """Parse JSON from Gemini response and validate. Returns (data, error)."""
    parsed = safe_parse_json(raw_text)
    if parsed is None:
        return None, f"Attempt {attempt}: Could not parse JSON from Gemini response."

    is_valid, issues = validate_lesson_data(parsed)
    if not is_valid:
        if len(issues) <= 2:
            return _fill_defaults(parsed), None
        return None, f"Attempt {attempt}: Validation issues: {'; '.join(issues)}"

    return parsed, None


# ─────────────────────────────────────────────
# Mode 1: Text-based processing
# ─────────────────────────────────────────────

def process_lesson_content(lesson_text: str) -> dict:
    """
    Send lesson TEXT to Gemini and get structured educational output.
    Tries multiple models if rate-limited.
    """
    _configure_api()
    prompt = LESSON_PROCESSING_PROMPT.format(lesson_content=lesson_text)

    last_error: Optional[str] = None

    for model_name in MODEL_NAMES:
        model = _create_model(model_name)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = model.generate_content(prompt)
                if not response or not response.text:
                    last_error = "Gemini returned an empty response."
                    continue

                data, error = _parse_and_validate(response.text, attempt)
                if data:
                    return data
                last_error = error

            except Exception as e:
                error_str = str(e)
                last_error = f"[{model_name}] Attempt {attempt}: {error_str}"
                # If rate-limited, try next model instead of retrying same one
                if "429" in error_str or "quota" in error_str.lower():
                    time.sleep(2)
                    break  # break inner loop, try next model
                continue

    raise RuntimeError(
        f"Failed to process lesson after trying all models.\n"
        f"Last error: {last_error}\n\n"
        "Your API quota may be exhausted. Wait a minute and try again,\n"
        "or check your quota at: https://ai.google.dev/gemini-api/docs/rate-limits"
    )


# ─────────────────────────────────────────────
# Mode 2: Multimodal PDF processing (File API)
# ─────────────────────────────────────────────

def process_lesson_from_pdf(file_path: Path) -> dict:
    """
    Upload a scanned PDF directly to Gemini via the File API,
    then use Gemini Vision to read and process it.
    Tries multiple models if rate-limited.
    """
    _configure_api()

    last_error: Optional[str] = None

    # Upload the PDF once (shared across model retries)
    try:
        uploaded_file = genai.upload_file(
            path=str(file_path),
            mime_type="application/pdf",
        )

        # Wait for file processing to complete
        while uploaded_file.state.name == "PROCESSING":
            time.sleep(2)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state.name == "FAILED":
            raise RuntimeError("Gemini failed to process the uploaded PDF file.")

    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to upload PDF to Gemini: {str(e)}")

    # Try each model
    for model_name in MODEL_NAMES:
        model = _create_model(model_name)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = model.generate_content([PDF_PROCESSING_PROMPT, uploaded_file])

                if not response or not response.text:
                    last_error = f"[{model_name}] Attempt {attempt}: Empty response."
                    continue

                data, error = _parse_and_validate(response.text, attempt)
                if data:
                    # Clean up
                    try:
                        genai.delete_file(uploaded_file.name)
                    except Exception:
                        pass
                    return data
                last_error = error

            except Exception as e:
                error_str = str(e)
                last_error = f"[{model_name}] Attempt {attempt}: {error_str}"
                if "429" in error_str or "quota" in error_str.lower():
                    time.sleep(2)
                    break  # try next model
                continue

    # Clean up on failure
    try:
        genai.delete_file(uploaded_file.name)
    except Exception:
        pass

    raise RuntimeError(
        f"Failed to process scanned PDF after trying all models.\n"
        f"Last error: {last_error}\n\n"
        "Your API quota may be exhausted. Wait a minute and try again."
    )


# ─────────────────────────────────────────────
# Mode 3: Video lesson (File API)
# ─────────────────────────────────────────────

def process_lesson_from_video(file_path: Path) -> dict:
    """
    Upload a video (MP4/MOV) to Gemini via the File API, wait until ACTIVE,
    then process with a video-specific prompt (includes visual_frame_captions).
    """
    _configure_api()

    last_error: Optional[str] = None

    try:
        uploaded_file = upload_video_and_wait_active(file_path)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Failed to upload video to Gemini: {str(e)}")

    for model_name in MODEL_NAMES:
        model = _create_model(model_name)
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = model.generate_content([VIDEO_PROCESSING_PROMPT, uploaded_file])

                if not response or not response.text:
                    last_error = f"[{model_name}] Attempt {attempt}: Empty response."
                    continue

                data, error = _parse_and_validate(response.text, attempt)
                if data:
                    try:
                        genai.delete_file(uploaded_file.name)
                    except Exception:
                        pass
                    return data
                last_error = error

            except Exception as e:
                error_str = str(e)
                last_error = f"[{model_name}] Attempt {attempt}: {error_str}"
                if "429" in error_str or "quota" in error_str.lower():
                    time.sleep(2)
                    break
                continue

    try:
        genai.delete_file(uploaded_file.name)
    except Exception:
        pass

    raise RuntimeError(
        f"Failed to process video after trying all models.\n"
        f"Last error: {last_error}\n\n"
        "Your API quota may be exhausted. Wait a minute and try again."
    )


def _fill_defaults(data: dict) -> dict:
    """Fill in any missing fields with sensible defaults."""
    defaults = {
        "title": "Untitled Lesson",
        "summary": "Summary not available.",
        "key_concepts": ["No concepts extracted"],
        "simplified_explanation": "Simplified explanation not available.",
        "audio_script": "Audio script not available.",
        "visual_summary": ["No visual summary available"],
        "quiz": [
            {
                "question": "No quiz questions were generated.",
                "options": ["N/A", "N/A", "N/A", "N/A"],
                "answer": "N/A",
            }
        ],
        "visual_frame_captions": [],
    }
    for key, default_value in defaults.items():
        if key not in data or not data[key]:
            data[key] = default_value
    return data
