"""
Lesson parser module.
Structures the raw AI output into organized lesson sections
for display and adaptation.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class LessonData:
    """Structured container for all lesson data from Gemini."""
    title: str = "Untitled Lesson"
    summary: str = ""
    key_concepts: list[str] = field(default_factory=list)
    simplified_explanation: str = ""
    audio_script: str = ""
    visual_summary: list[str] = field(default_factory=list)
    visual_frame_captions: list[str] = field(default_factory=list)
    quiz: list[dict] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if the lesson has minimum required content."""
        return bool(self.title and self.summary and self.quiz)

    def to_dict(self) -> dict:
        """Plain dict for APIs / Flutter migration (JSON-serializable values)."""
        return {
            "title": self.title,
            "summary": self.summary,
            "key_concepts": list(self.key_concepts),
            "simplified_explanation": self.simplified_explanation,
            "audio_script": self.audio_script,
            "visual_summary": list(self.visual_summary),
            "visual_frame_captions": list(self.visual_frame_captions),
            "quiz": [dict(q) for q in self.quiz],
        }


def parse_gemini_output(raw_data: dict) -> LessonData:
    """
    Convert raw Gemini JSON dict into a structured LessonData object.
    Applies type safety and default values.
    """
    return LessonData(
        title=_safe_str(raw_data.get("title"), "Untitled Lesson"),
        summary=_safe_str(raw_data.get("summary"), "No summary available."),
        key_concepts=_safe_list(raw_data.get("key_concepts")),
        simplified_explanation=_safe_str(
            raw_data.get("simplified_explanation"),
            "No simplified explanation available."
        ),
        audio_script=_safe_str(
            raw_data.get("audio_script"),
            "No audio script available."
        ),
        visual_summary=_safe_list(raw_data.get("visual_summary")),
        visual_frame_captions=_safe_list(raw_data.get("visual_frame_captions")),
        quiz=_safe_quiz(raw_data.get("quiz")),
    )


def get_section(lesson: LessonData, section_name: str) -> Optional[str | list]:
    """
    Retrieve a specific section from the lesson data by name.
    Returns None if the section doesn't exist.
    """
    section_map = {
        "title": lesson.title,
        "summary": lesson.summary,
        "key_concepts": lesson.key_concepts,
        "simplified_explanation": lesson.simplified_explanation,
        "audio_script": lesson.audio_script,
        "visual_summary": lesson.visual_summary,
        "visual_frame_captions": lesson.visual_frame_captions,
        "quiz": lesson.quiz,
    }
    return section_map.get(section_name)


# --- Private helpers ---

def _safe_str(value, default: str = "") -> str:
    """Safely convert a value to string."""
    if value is None:
        return default
    return str(value).strip() or default


def _safe_list(value) -> list[str]:
    """Safely convert a value to a list of strings."""
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if item]


def _safe_quiz(value) -> list[dict]:
    """Validate and return quiz questions list."""
    if not isinstance(value, list):
        return []

    valid_questions: list[dict] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        if all(k in item for k in ("question", "options", "answer")):
            # Ensure options is a list of 4 strings
            options = item.get("options", [])
            if isinstance(options, list) and len(options) == 4:
                valid_questions.append({
                    "question": str(item["question"]),
                    "options": [str(o) for o in options],
                    "answer": str(item["answer"]),
                })

    return valid_questions
