"""
Progress tracker module.
Tracks student quiz scores and lesson history using local JSON storage.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional

PROGRESS_FILE = Path("data/student_progress.json")


def _load_progress() -> list[dict]:
    """Load progress data from the JSON file."""
    try:
        if PROGRESS_FILE.exists():
            content = PROGRESS_FILE.read_text(encoding="utf-8")
            data = json.loads(content)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, IOError):
        pass
    return []


def _save_progress(progress: list[dict]) -> None:
    """Save progress data to the JSON file."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(
        json.dumps(progress, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def save_quiz_result(
    lesson_title: str,
    score: int,
    total: int,
    mode: Optional[str] = None,
) -> None:
    """
    Save a quiz result to the progress file.
    
    Args:
        lesson_title: Title of the lesson taken.
        score: Number of correct answers.
        total: Total number of questions.
        mode: The accessibility mode used (if any).
    """
    progress = _load_progress()
    entry = {
        "lesson_title": lesson_title,
        "score": score,
        "total": total,
        "percentage": round((score / total) * 100, 1) if total > 0 else 0,
        "mode": mode or "standard",
        "timestamp": datetime.now().isoformat(),
    }
    progress.append(entry)

    # Keep only the last 50 entries
    if len(progress) > 50:
        progress = progress[-50:]

    _save_progress(progress)


def get_progress_summary() -> dict:
    """
    Get a summary of student progress.
    
    Returns:
        Dict with keys: total_quizzes, average_score, recent_results, best_score
    """
    progress = _load_progress()

    if not progress:
        return {
            "total_quizzes": 0,
            "average_score": 0,
            "recent_results": [],
            "best_score": 0,
        }

    percentages = [entry.get("percentage", 0) for entry in progress]

    return {
        "total_quizzes": len(progress),
        "average_score": round(sum(percentages) / len(percentages), 1),
        "recent_results": progress[-5:],  # Last 5 results
        "best_score": max(percentages),
    }


def clear_progress() -> None:
    """Clear all progress data."""
    _save_progress([])
