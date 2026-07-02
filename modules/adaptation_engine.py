"""
Adaptation engine module.
Provides accessibility mode metadata and Streamlit rendering
for different learning needs.

Supported modes:
  - Dyslexia Support
  - Visual Support (for visually impaired learners)
  - Hearing Support (for hearing-impaired learners)
  - Slow Learner Support
"""

import streamlit as st


# Mode definitions with descriptions and icons
ACCESSIBILITY_MODES = {
    "dyslexia": {
        "label": "🔤 Dyslexia Support",
        "description": "Simplified language with bullet-point concepts for easier reading.",
        "icon": "🔤",
    },
    "visual": {
        "label": "👁️ Visual Support",
        "description": "Audio-friendly scripts and structured readable content.",
        "icon": "👁️",
    },
    "hearing": {
        "label": "👂 Hearing Support",
        "description": "Text summaries, visual points, and written key concepts.",
        "icon": "👂",
    },
    "slow_learner": {
        "label": "🐢 Slow Learner Support",
        "description": "Content broken into small digestible chunks, one concept at a time.",
        "icon": "🐢",
    },
}


def render_adapted_content(lesson, mode: str) -> None:
    """Render lesson content adapted to the selected accessibility mode.

    Args:
        lesson: A LessonData instance with all AI-generated content.
        mode: One of the keys in ACCESSIBILITY_MODES.
    """
    mode_info = ACCESSIBILITY_MODES.get(mode)
    if not mode_info:
        st.warning("Unknown accessibility mode selected.")
        return

    st.markdown(
        f"<h3 style='color:#283593;'>{mode_info['label']}</h3>"
        f"<p style='color:#666; margin-bottom:1rem;'>{mode_info['description']}</p>",
        unsafe_allow_html=True,
    )

    if mode == "dyslexia":
        _render_dyslexia(lesson)
    elif mode == "visual":
        _render_visual(lesson)
    elif mode == "hearing":
        _render_hearing(lesson)
    elif mode == "slow_learner":
        _render_slow_learner(lesson)


# ── Mode-specific renderers ──────────────────────────────


def _render_dyslexia(lesson) -> None:
    """Dyslexia-friendly: simplified text + bullet-point key concepts."""
    st.markdown(
        f"""<div style="
            font-size: 1.15rem;
            line-height: 2;
            padding: 1.2rem;
            background: #FFFDE7;
            border-radius: 12px;
            color: #333;
            letter-spacing: 0.02em;
        ">{lesson.simplified_explanation}</div>""",
        unsafe_allow_html=True,
    )

    if lesson.key_concepts:
        st.markdown("#### 🔑 Key Concepts")
        for concept in lesson.key_concepts:
            st.markdown(
                f"""<div style="
                    padding: 0.6rem 1rem;
                    margin: 0.35rem 0;
                    background: #FFF9C4;
                    border-left: 4px solid #F9A825;
                    border-radius: 0 8px 8px 0;
                    font-size: 1.05rem;
                    color: #333;
                ">• {concept}</div>""",
                unsafe_allow_html=True,
            )


def _render_visual(lesson) -> None:
    """Visual support: audio script for screen readers + structured summary."""
    st.info("🎧 The content below is optimized for screen readers and text-to-speech.")

    st.markdown("#### 🎧 Audio Script")
    st.markdown(
        f"""<div style="
            font-size: 1.1rem;
            line-height: 1.9;
            padding: 1.2rem;
            background: #E8EAF6;
            border-radius: 12px;
            color: #1A237E;
        ">{lesson.audio_script}</div>""",
        unsafe_allow_html=True,
    )

    st.markdown("#### 📄 Summary")
    st.markdown(lesson.summary)


def _render_hearing(lesson) -> None:
    """Hearing support: rich text summaries + visual points."""
    st.markdown("#### 📄 Detailed Summary")
    st.markdown(
        f"""<div style="
            font-size: 1.05rem;
            line-height: 1.85;
            padding: 1.2rem;
            background: #E0F7FA;
            border-radius: 12px;
            color: #004D40;
        ">{lesson.summary}</div>""",
        unsafe_allow_html=True,
    )

    if lesson.visual_summary:
        st.markdown("#### 🖼️ Visual Points")
        cols = st.columns(min(len(lesson.visual_summary), 3))
        for i, point in enumerate(lesson.visual_summary):
            with cols[i % len(cols)]:
                st.markdown(
                    f"""<div style="
                        background: linear-gradient(135deg, #E0F2F1, #B2DFDB);
                        padding: 1.2rem;
                        border-radius: 12px;
                        text-align: center;
                        min-height: 90px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: #00695C;
                        margin-bottom: 0.5rem;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    ">{point}</div>""",
                    unsafe_allow_html=True,
                )

    if lesson.key_concepts:
        st.markdown("#### 🔑 Key Concepts")
        for concept in lesson.key_concepts:
            st.markdown(f"- {concept}")


def _render_slow_learner(lesson) -> None:
    """Slow learner: chunked content, one concept at a time."""
    st.markdown("#### 📖 Lesson Summary")
    st.markdown(lesson.summary)

    if lesson.key_concepts:
        st.markdown("#### 🧩 One Concept at a Time")
        for i, concept in enumerate(lesson.key_concepts, 1):
            with st.expander(f"Concept {i}", expanded=(i == 1)):
                st.markdown(
                    f"""<div style="
                        font-size: 1.1rem;
                        line-height: 1.9;
                        padding: 1rem;
                        background: #F3E5F5;
                        border-radius: 10px;
                        color: #4A148C;
                    ">{concept}</div>""",
                    unsafe_allow_html=True,
                )

    st.markdown("#### ✨ Simplified Explanation")
    st.markdown(
        f"""<div style="
            font-size: 1.1rem;
            line-height: 2;
            padding: 1.2rem;
            background: #FFF3E0;
            border-radius: 12px;
            color: #333;
        ">{lesson.simplified_explanation}</div>""",
        unsafe_allow_html=True,
    )
