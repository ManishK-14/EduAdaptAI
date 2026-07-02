"""
Video preprocessing via the Gemini File API (same stack as PDF multimodal).

1. genai.upload_file — sends the video to Google for ingestion.
2. Poll genai.get_file until state is ACTIVE (Gemini-side preprocessing/encoding).
3. The caller (gemini_service.process_lesson_from_video) passes the file handle to
   model.generate_content(...) with VIDEO_PROCESSING_PROMPT so Gemini returns
   lesson JSON plus visual_frame_captions (timestamped scene captions).

No separate caption pipeline — captions come only from that Gemini response.
"""

import os
import time
from pathlib import Path

import google.generativeai as genai
from dotenv import load_dotenv


def _configure_gemini() -> None:
    """Same API key as gemini_service (this module cannot import gemini_service — circular)."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() == "" or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Gemini API key not configured. Set GEMINI_API_KEY in your .env file."
        )
    genai.configure(api_key=api_key)


def _mime_type_for_video(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".mp4":
        return "video/mp4"
    if suf in (".mov", ".qt"):
        return "video/quicktime"
    raise ValueError(f"Unsupported video extension: {suf!r}. Use .mp4 or .mov.")


def upload_video_and_wait_active(file_path: Path, poll_interval_sec: float = 2.0):
    """
    Upload a video via Gemini File API and poll until Gemini finishes preprocessing (ACTIVE).

    Returns the uploaded file object for use in generate_content (captions + lesson JSON).
    """
    _configure_gemini()

    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Video file not found: {path}")

    mime = _mime_type_for_video(path)
    uploaded = genai.upload_file(path=str(path), mime_type=mime)

    max_attempts = 300  # ~10 minutes at 2s interval
    attempts = 0
    while uploaded.state.name != "ACTIVE":
        if uploaded.state.name == "FAILED":
            raise RuntimeError("Gemini failed to process the uploaded video file.")
        attempts += 1
        if attempts > max_attempts:
            raise RuntimeError(
                "Timed out waiting for the uploaded video to reach ACTIVE state in Gemini."
            )
        time.sleep(poll_interval_sec)
        uploaded = genai.get_file(uploaded.name)

    return uploaded
