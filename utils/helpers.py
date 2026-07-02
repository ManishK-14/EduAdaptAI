"""
Utility helper functions used across the application.
"""

import json
import re
from typing import Optional, Any
from pathlib import Path


def clean_json_response(raw_text: str) -> str:
    """
    Clean a raw Gemini response to extract valid JSON.
    Handles common issues like markdown code fences, leading/trailing text, etc.
    """
    text = raw_text.strip()

    # Remove markdown code fences (```json ... ``` or ``` ... ```)
    text = re.sub(r"^```(?:json)?\s*\n?", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n?```\s*$", "", text, flags=re.MULTILINE)

    # Try to find a JSON object in the text
    # Look for the first { and the last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")

    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace : last_brace + 1]

    return text.strip()


def safe_parse_json(raw_text: str) -> Optional[dict]:
    """
    Attempt to parse JSON from a raw string with multiple fallback strategies.
    Returns parsed dict or None if all strategies fail.
    """
    # Strategy 1: direct parse
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: clean then parse
    cleaned = clean_json_response(raw_text)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Try fixing common issues — trailing commas, single quotes
    try:
        # Replace single quotes with double quotes (crude but sometimes works)
        fixed = cleaned.replace("'", '"')
        # Remove trailing commas before closing braces/brackets
        fixed = re.sub(r",\s*([}\]])", r"\1", fixed)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    return None


def validate_lesson_data(data: dict) -> tuple[bool, list[str]]:
    """
    Validate that parsed lesson data contains all required fields
    with the expected types and structure.
    Returns (is_valid, list_of_issues).
    """
    issues: list[str] = []
    required_fields = {
        "title": str,
        "summary": str,
        "key_concepts": list,
        "simplified_explanation": str,
        "audio_script": str,
        "visual_summary": list,
        "quiz": list,
    }

    for field, expected_type in required_fields.items():
        if field not in data:
            issues.append(f"Missing required field: '{field}'")
        elif not isinstance(data[field], expected_type):
            issues.append(
                f"Field '{field}' should be {expected_type.__name__}, got {type(data[field]).__name__}"
            )

    # Validate quiz structure
    if "quiz" in data and isinstance(data["quiz"], list):
        for i, q in enumerate(data["quiz"]):
            if not isinstance(q, dict):
                issues.append(f"Quiz question {i+1} is not a valid object")
                continue
            if "question" not in q:
                issues.append(f"Quiz question {i+1} missing 'question' field")
            if "options" not in q:
                issues.append(f"Quiz question {i+1} missing 'options' field")
            elif not isinstance(q["options"], list) or len(q["options"]) != 4:
                issues.append(f"Quiz question {i+1} must have exactly 4 options")
            if "answer" not in q:
                issues.append(f"Quiz question {i+1} missing 'answer' field")
            elif "options" in q and isinstance(q["options"], list):
                if q["answer"] not in q["options"]:
                    issues.append(
                        f"Quiz question {i+1}: answer doesn't match any option"
                    )

    if "visual_frame_captions" in data and not isinstance(data["visual_frame_captions"], list):
        issues.append(
            "Field 'visual_frame_captions' should be list, "
            f"got {type(data['visual_frame_captions']).__name__}"
        )

    return (len(issues) == 0, issues)


def truncate_text(text: str, max_chars: int = 15000) -> str:
    """Truncate text to a maximum character count, preserving word boundaries."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    # Cut at last space to avoid splitting a word
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.8:
        truncated = truncated[:last_space]
    return truncated + "\n\n[Content truncated for processing...]"


def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def chunk_text(text: str, chunk_size: int = 3) -> list[str]:
    """
    Split text into chunks of N sentences each.
    Useful for slow-learner mode where content is presented piece by piece.
    """
    # Split on sentence-ending punctuation followed by a space or newline
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks: list[str] = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i : i + chunk_size])
        chunks.append(chunk)

    return chunks if chunks else [text]
