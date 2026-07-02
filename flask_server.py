"""
Flask REST API for EduAdapt AI (Gemini lesson processing, quiz scoring, progress).

Run from the `inclusive-learning-ai` directory (same as Streamlit) so `.env` and `data/` resolve:

    pip install -r requirements.txt
    python flask_server.py

Or:

    flask --app flask_server:app run --host 0.0.0.0 --port 5000
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

load_dotenv()

from modules.file_processor import (
    MAX_FILE_SIZE_MB,
    extract_text_from_pdf,
    process_text_input,
    UPLOAD_DIR,
)
from modules.gemini_service import (
    process_lesson_content,
    process_lesson_from_pdf,
    process_lesson_from_video,
)
from modules.lesson_parser import parse_gemini_output
from modules.progress_tracker import get_progress_summary, save_quiz_result
from modules.quiz_engine import score_quiz_submission
from utils.helpers import ensure_directory

# Accessibility metadata (same labels as Streamlit UI)
from modules.adaptation_engine import ACCESSIBILITY_MODES

MAX_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_BYTES
CORS(app)


def _err(message: str, code: int = 400):
    return jsonify({"ok": False, "error": message}), code


def _ok(payload: dict, code: int = 200):
    out = {"ok": True, **payload}
    return jsonify(out), code


def _lesson_response(raw: dict):
    lesson = parse_gemini_output(raw)
    if not lesson.is_valid:
        return _err("AI returned incomplete lesson data (missing title, summary, or quiz).", 422)
    return _ok({"lesson": lesson.to_dict()})


def _save_upload_file() -> Path:
    """Save multipart `file` field to UPLOAD_DIR; validate size."""
    if "file" not in request.files:
        raise ValueError("Missing multipart field 'file'.")
    f = request.files["file"]
    if not f or not f.filename:
        raise ValueError("Empty filename.")
    ensure_directory(UPLOAD_DIR)
    safe = secure_filename(f.filename)
    if not safe:
        raise ValueError("Invalid filename.")
    path = UPLOAD_DIR / safe
    f.save(path)
    if path.stat().st_size > MAX_BYTES:
        path.unlink(missing_ok=True)
        raise ValueError(f"File too large. Maximum is {MAX_FILE_SIZE_MB} MB.")
    return path


@app.route("/")
def index():
    return _ok(
        {
            "service": "EduAdapt AI API",
            "version": "1",
            "docs": "See GET /health and /api/v1/* routes.",
        }
    )


@app.get("/health")
def health():
    return jsonify({"status": "ok", "gemini_configured": bool(os.getenv("GEMINI_API_KEY", "").strip())})


@app.post("/api/v1/process/text")
def api_process_text():
    """JSON body: { \"text\": \"...\" } (min 20 characters)."""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if len(text) < 20:
        return _err("Field 'text' must be at least 20 characters.", 400)
    processed = process_text_input(text)
    if not processed:
        return _err("Text too short after cleaning.", 400)
    try:
        raw = process_lesson_content(processed)
        return _lesson_response(raw)
    except RuntimeError as e:
        return _err(str(e), 502)
    except Exception as e:
        app.logger.exception("process/text")
        return _err(str(e), 500)


@app.post("/api/v1/process/pdf")
def api_process_pdf():
    """
    Multipart form: `file` = .pdf or .txt lesson file.
    Text-based PDF/TXT → text pipeline; scanned PDF → Gemini File API (vision).
    """
    try:
        path = _save_upload_file()
    except ValueError as e:
        return _err(str(e), 400)

    name = path.name.lower()
    try:
        if name.endswith(".pdf"):
            extracted = extract_text_from_pdf(path)
            if extracted:
                raw = process_lesson_content(extracted)
            else:
                raw = process_lesson_from_pdf(path)
        elif name.endswith(".txt"):
            content = path.read_text(encoding="utf-8", errors="ignore")
            processed = process_text_input(content)
            if not processed:
                return _err("Text file is empty or too short.", 400)
            raw = process_lesson_content(processed)
        else:
            path.unlink(missing_ok=True)
            return _err("Only .pdf or .txt files are allowed for this endpoint.", 400)
        return _lesson_response(raw)
    except RuntimeError as e:
        return _err(str(e), 502)
    except ValueError as e:
        return _err(str(e), 400)
    except Exception as e:
        app.logger.exception("process/pdf")
        return _err(str(e), 500)


@app.post("/api/v1/process/video")
def api_process_video():
    """Multipart form: `file` = .mp4 or .mov (max 20 MB)."""
    try:
        path = _save_upload_file()
    except ValueError as e:
        return _err(str(e), 400)

    name = path.name.lower()
    if not (name.endswith(".mp4") or name.endswith(".mov")):
        path.unlink(missing_ok=True)
        return _err("Only .mp4 or .mov files are allowed.", 400)

    try:
        raw = process_lesson_from_video(path)
        return _lesson_response(raw)
    except RuntimeError as e:
        return _err(str(e), 502)
    except Exception as e:
        app.logger.exception("process/video")
        return _err(str(e), 500)


@app.post("/api/v1/quiz/score")
def api_quiz_score():
    """
    JSON body: { \"quiz\": [ { \"question\", \"options\", \"answer\" }, ... ], \"answers\": [ \"...\", ... ] }
    Each answers[i] is the selected option text for quiz[i].
    """
    data = request.get_json(silent=True) or {}
    quiz = data.get("quiz")
    answers = data.get("answers")
    if not isinstance(quiz, list) or not quiz:
        return _err("Field 'quiz' must be a non-empty list.", 400)
    if not isinstance(answers, list):
        return _err("Field 'answers' must be a list.", 400)
    for i, q in enumerate(quiz):
        if not isinstance(q, dict) or "answer" not in q:
            return _err(f"Invalid quiz item at index {i}.", 400)
    try:
        result = score_quiz_submission(quiz, [str(a) for a in answers])
        return _ok({"result": result})
    except Exception as e:
        app.logger.exception("quiz/score")
        return _err(str(e), 500)


@app.get("/api/v1/progress")
def api_progress_get():
    return _ok({"progress": get_progress_summary()})


@app.post("/api/v1/progress/quiz")
def api_progress_quiz():
    """
    JSON body: { \"lesson_title\": str, \"score\": int, \"total\": int, \"mode\": str optional }
    """
    data = request.get_json(silent=True) or {}
    title = (data.get("lesson_title") or "").strip()
    score = data.get("score")
    total = data.get("total")
    mode = data.get("mode")
    if not title:
        return _err("Field 'lesson_title' is required.", 400)
    try:
        score = int(score)
        total = int(total)
    except (TypeError, ValueError):
        return _err("Fields 'score' and 'total' must be integers.", 400)
    if total <= 0 or score < 0 or score > total:
        return _err("Invalid score or total.", 400)
    save_quiz_result(title, score, total, mode=str(mode) if mode else None)
    return _ok({"saved": True, "progress": get_progress_summary()})


@app.get("/api/v1/accessibility-modes")
def api_accessibility_modes():
    """Same keys/labels as the Streamlit accessibility selector."""
    modes = [
        {"key": key, **{k: v for k, v in info.items() if k in ("label", "description", "icon")}}
        for key, info in ACCESSIBILITY_MODES.items()
    ]
    return _ok({"modes": modes})


@app.errorhandler(413)
def too_large(_e):
    return _err(f"Payload too large. Maximum upload size is {MAX_FILE_SIZE_MB} MB.", 413)


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes"))
