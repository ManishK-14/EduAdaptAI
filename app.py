"""
EduAdapt AI — Inclusive Learning Platform
Main Streamlit Application

Teach once. Adapt for every learner.
"""

import streamlit as st

# --- Page Configuration (must be FIRST Streamlit command) ---
st.set_page_config(
    page_title="EduAdapt AI — Inclusive Learning",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

from pathlib import Path

from modules.file_processor import (
    MAX_FILE_SIZE_MB,
    process_uploaded_file,
    process_text_input,
    save_uploaded_file,
)
from modules.gemini_service import (
    process_lesson_content,
    process_lesson_from_pdf,
    process_lesson_from_video,
)
from modules.lesson_parser import LessonData, parse_gemini_output
from modules.adaptation_engine import ACCESSIBILITY_MODES, render_adapted_content
from modules.quiz_engine import render_quiz
from modules.progress_tracker import get_progress_summary, save_quiz_result


# ─────────────────────────────────────────────
# Custom CSS for polished UI
# ─────────────────────────────────────────────
def inject_custom_css():
    st.markdown("""
    <style>
        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        /* Global font */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Hero header */
        .hero-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            color: white;
            margin-bottom: 1.5rem;
            box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        }
        .hero-header h1 {
            margin: 0;
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        .hero-header p {
            margin: 0.4rem 0 0 0;
            font-size: 1.1rem;
            opacity: 0.9;
            font-weight: 300;
        }

        /* Stat cards */
        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 1.2rem 1rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .stat-card .stat-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #333;
        }
        .stat-card .stat-label {
            font-size: 0.85rem;
            color: #666;
            margin-top: 0.2rem;
        }

        /* Mode cards */
        .mode-card {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .mode-card:hover {
            border-color: #667eea;
            box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
            transform: translateY(-2px);
        }

        /* Section headers */
        .section-header {
            font-size: 1.4rem;
            font-weight: 600;
            color: #333;
            margin: 1.5rem 0 0.8rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 3px solid #667eea;
            display: inline-block;
        }

        /* Sidebar styling — premium deep indigo gradient */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #1e1b4b 0%, #312e81 50%, #3730a3 100%) !important;
            color: #e0e7ff !important;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] small,
        [data-testid="stSidebar"] [data-testid="stCaption"],
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
            color: #e0e7ff !important;
        }
        [data-testid="stSidebar"] .stRadio label,
        [data-testid="stSidebar"] [data-baseweb="radio"] label {
            color: #e0e7ff !important;
        }
        [data-testid="stSidebar"] [data-testid="stMetricValue"],
        [data-testid="stSidebar"] [data-testid="stMetricLabel"],
        [data-testid="stSidebar"] [data-testid="stMetricDelta"] {
            color: #e0e7ff !important;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(224, 231, 255, 0.2) !important;
        }
        [data-testid="stSidebar"] [data-testid="stExpander"] {
            background: rgba(255, 255, 255, 0.06);
            border-radius: 8px;
            border: 1px solid rgba(224, 231, 255, 0.15);
        }

        /* Button styling */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 10px;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            transition: all 0.3s ease;
        }

        /* Info box */
        .info-box {
            background: #EDE7F6;
            border-left: 4px solid #7C4DFF;
            padding: 1rem 1.2rem;
            border-radius: 0 10px 10px 0;
            margin: 0.5rem 0;
            color: #311B92;
        }

        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Initialize session state
# ─────────────────────────────────────────────
def init_session_state():
    defaults = {
        "lesson_data": None,
        "raw_text": "",
        "processing_complete": False,
        "lesson_dict": None,
        "last_quiz_score": None,
        "last_quiz_total": None,
        "selected_mode": "dyslexia",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ─────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────
def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎓 EduAdapt AI")
        st.caption("Inclusive Learning Platform")
        st.divider()

        # Input mode selection
        st.markdown("### 📥 Input Method")
        input_mode = st.radio(
            "Choose how to provide lesson content:",
            options=["📄 Upload PDF", "✏️ Paste Text", "🎥 Video"],
            key="input_mode_radio",
            label_visibility="collapsed",
        )

        st.divider()

        # Progress section
        st.markdown("### 📊 Your Progress")
        progress = get_progress_summary()

        if progress["total_quizzes"] > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Quizzes Taken", progress["total_quizzes"])
            with col2:
                st.metric("Avg Score", f"{progress['average_score']}%")

            st.metric("Best Score", f"{progress['best_score']}%")

            if progress["recent_results"]:
                with st.expander("Recent Results"):
                    for result in reversed(progress["recent_results"]):
                        st.markdown(
                            f"• **{result['lesson_title'][:30]}...** "
                            f"— {result['score']}/{result['total']} "
                            f"({result['percentage']}%)"
                        )
        else:
            st.caption("No quiz results yet. Take a quiz to track progress!")

        st.divider()
        st.markdown(
            "<div style='text-align:center; color:#888; font-size:0.8rem;'>"
            "Built with ❤️ for inclusive education<br>"
            "Powered by Gemini AI"
            "</div>",
            unsafe_allow_html=True,
        )

    return input_mode


# ─────────────────────────────────────────────
# Hero Header
# ─────────────────────────────────────────────
def render_hero():
    st.markdown("""
    <div class="hero-header">
        <h1>🎓 EduAdapt AI</h1>
        <p>Teach once. Adapt for every learner.</p>
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# Lesson Input Section
# ─────────────────────────────────────────────
def render_input_section(input_mode: str) -> tuple[str | None, Path | None, Path | None]:
    """
    Returns (extracted_text, pdf_file_path, video_file_path).
    Priority when processing: text → video → scanned PDF.
    """
    st.markdown('<div class="section-header">📥 Lesson Input</div>', unsafe_allow_html=True)

    extracted_text = None
    pdf_path = None
    video_path = None

    if "Upload PDF" in input_mode:
        uploaded_file = st.file_uploader(
            "Upload a lesson file (PDF or TXT)",
            type=["pdf", "txt"],
            key="file_uploader",
            help="Maximum file size: 20 MB. Supports both text-based and scanned PDFs.",
        )
        if uploaded_file:
            try:
                with st.spinner("📄 Extracting text from file..."):
                    text, file_path = process_uploaded_file(uploaded_file)

                if text:
                    # Text extraction succeeded
                    extracted_text = text
                    st.success(f"✅ Extracted {len(text):,} characters from '{uploaded_file.name}'")
                    with st.expander("👀 Preview extracted text", expanded=False):
                        st.text(text[:2000] + ("..." if len(text) > 2000 else ""))
                else:
                    # Scanned/image PDF — text extraction failed, will use multimodal
                    pdf_path = file_path
                    st.info(
                        f"📷 **'{uploaded_file.name}'** appears to be a scanned/image-based PDF. "
                        "Gemini AI will read it directly using Vision when you click Process."
                    )

            except (ValueError, RuntimeError) as e:
                st.error(f"❌ {str(e)}")

    elif "Paste Text" in input_mode:
        text_input = st.text_area(
            "Paste your lesson content below:",
            height=250,
            placeholder="Paste or type your lesson content here...\n\nMinimum 20 characters required.",
            key="text_input_area",
        )
        if text_input:
            processed = process_text_input(text_input)
            if processed:
                extracted_text = processed
                st.success(f"✅ Ready to process ({len(extracted_text):,} characters)")
            else:
                st.warning("⚠️ Please enter at least 20 characters of lesson content.")

    else:  # Video
        st.caption("MP4 or MOV, max 20 MB.")
        video_file = st.file_uploader(
            "Upload a lesson video",
            type=["mp4", "mov"],
            key="video_uploader",
            help="Gemini analyzes the video and returns frame captions plus the full lesson.",
        )
        if video_file:
            try:
                size_mb = video_file.size / (1024 * 1024)
                if size_mb > MAX_FILE_SIZE_MB:
                    raise ValueError(
                        f"File too large ({size_mb:.1f} MB). Maximum is {MAX_FILE_SIZE_MB} MB."
                    )
                video_path = save_uploaded_file(video_file)
                st.success(f"✅ Video ready: **{video_file.name}**")
            except ValueError as e:
                st.error(f"❌ {str(e)}")

    return extracted_text, pdf_path, video_path


# ─────────────────────────────────────────────
# AI Processing Section
# ─────────────────────────────────────────────
def render_processing_section(
    extracted_text: str | None,
    pdf_path: Path | None,
    video_path: Path | None,
):
    """
    Text → Gemini text; Video → File API + video prompt; Scanned PDF → PDF vision.
    """
    st.markdown('<div class="section-header">🤖 AI Processing</div>', unsafe_allow_html=True)

    has_input = (
        (extracted_text is not None)
        or (pdf_path is not None)
        or (video_path is not None)
    )
    will_use_text = extracted_text is not None
    will_use_video = (not will_use_text) and (video_path is not None)
    will_use_scanned_pdf = (not will_use_text) and (not will_use_video) and (pdf_path is not None)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if will_use_scanned_pdf:
            btn_label = "🚀 Process Scanned PDF with Gemini Vision"
        elif will_use_video:
            btn_label = "🚀 Process Video with Gemini AI"
        else:
            btn_label = "🚀 Process with Gemini AI"
        process_btn = st.button(
            btn_label,
            use_container_width=True,
            type="primary",
            disabled=(not has_input),
            key="process_button",
        )

    if process_btn and has_input:
        with st.status("🧠 Processing lesson with Gemini AI...", expanded=True) as status:
            try:
                if extracted_text is not None:
                    st.write("📤 Sending content to Gemini...")
                    raw_output = process_lesson_content(extracted_text)
                elif video_path is not None:
                    st.write("📤 Uploading video to Gemini File API...")
                    st.write("🎥 Waiting for ACTIVE, then analyzing video...")
                    raw_output = process_lesson_from_video(video_path)
                elif pdf_path is not None:
                    st.write("📤 Uploading PDF to Gemini File API...")
                    st.write("👁️ Gemini is reading the scanned pages (this may take 30-60 seconds)...")
                    raw_output = process_lesson_from_pdf(pdf_path)
                else:
                    st.error("No processable input.")
                    status.update(label="❌ Processing failed", state="error")
                    return

                st.write("🔍 Parsing and validating AI output...")
                lesson = parse_gemini_output(raw_output)

                if not lesson.is_valid:
                    st.error("⚠️ AI generated incomplete output. Please try again.")
                    status.update(label="❌ Processing failed", state="error")
                    return

                st.write("✅ Lesson processed successfully!")
                st.session_state["lesson_data"] = lesson
                st.session_state["lesson_dict"] = lesson.to_dict()
                st.session_state["processing_complete"] = True
                status.update(label="✅ Processing complete!", state="complete")

            except RuntimeError as e:
                st.error(f"❌ {str(e)}")
                status.update(label="❌ Processing failed", state="error")
            except Exception as e:
                st.error(f"❌ Unexpected error: {str(e)}")
                status.update(label="❌ Processing failed", state="error")


# ─────────────────────────────────────────────
# Lesson Output Section
# ─────────────────────────────────────────────
def render_lesson_output(lesson: LessonData):
    """Display all AI-generated lesson content in organized tabs."""
    st.markdown('<div class="section-header">📚 AI-Generated Lesson Content</div>', unsafe_allow_html=True)

    # Title
    st.markdown(
        f"""<div style="
            background: linear-gradient(135deg, #e8eaf6, #c5cae9);
            padding: 1.2rem 1.5rem;
            border-radius: 12px;
            margin-bottom: 1rem;
        "><h2 style="margin:0; color:#283593;">{lesson.title}</h2></div>""",
        unsafe_allow_html=True,
    )

    # Tabs for different outputs
    tab_summary, tab_concepts, tab_simple, tab_audio, tab_visual, tab_frames = st.tabs([
        "📄 Summary",
        "🔑 Key Concepts",
        "✨ Simplified",
        "🎧 Audio Script",
        "🖼️ Visual Summary",
        "🎬 Frame Captions",
    ])

    with tab_summary:
        st.markdown(lesson.summary)

    with tab_concepts:
        for i, concept in enumerate(lesson.key_concepts, 1):
            st.markdown(
                f"""<div style="
                    background: #E3F2FD;
                    padding: 0.8rem 1rem;
                    border-radius: 8px;
                    margin: 0.4rem 0;
                    border-left: 4px solid #1976D2;
                    display: flex;
                    align-items: center;
                    color: #0D47A1;
                "><strong style='margin-right: 0.5rem;'>{i}.</strong> {concept}</div>""",
                unsafe_allow_html=True,
            )

    with tab_simple:
        st.markdown(
            f"""<div style="
                font-size: 1.1rem;
                line-height: 1.9;
                padding: 1rem;
                background: #FFF8E1;
                border-radius: 12px;
                color: #333;
            ">{lesson.simplified_explanation}</div>""",
            unsafe_allow_html=True,
        )

    with tab_audio:
        st.info("🎧 This script is optimized for text-to-speech or read-aloud use.")

        # ── Text-to-Speech play button (browser SpeechSynthesis API) ──
        import json as _json
        import streamlit.components.v1 as _stcomp
        _safe_text = _json.dumps(lesson.audio_script)
        _stcomp.html(f"""
        <div style="display:flex; gap:0.6rem; align-items:center;">
            <button id="tts-play" onclick="toggleTTS()" style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #fff; border: none; padding: 0.55rem 1.4rem;
                border-radius: 10px; font-size: 0.95rem; cursor: pointer;
                font-weight: 600; display:inline-flex; align-items:center; gap:0.4rem;
                box-shadow: 0 4px 15px rgba(102,126,234,0.35);
                transition: all 0.25s ease;
            ">&#9654;&#65039; Play Audio</button>
            <button onclick="stopTTS()" style="
                background: #ef5350; color: #fff; border: none;
                padding: 0.55rem 1.1rem; border-radius: 10px;
                font-size: 0.95rem; cursor: pointer; font-weight: 600;
                box-shadow: 0 4px 15px rgba(239,83,80,0.25);
                transition: all 0.25s ease;
            ">&#9209; Stop</button>
        </div>
        <script>
            var ttsState = 'stopped';
            var ttsUtterance = null;
            var ttsKeepAlive = null;
            function toggleTTS() {{
                var btn = document.getElementById('tts-play');
                if (ttsState === 'stopped') {{
                    ttsUtterance = new SpeechSynthesisUtterance({_safe_text});
                    ttsUtterance.rate = 0.95;
                    ttsUtterance.pitch = 1.0;
                    ttsUtterance.onend = function() {{
                        ttsState = 'stopped';
                        btn.innerHTML = '&#9654;&#65039; Play Audio';
                        clearInterval(ttsKeepAlive);
                    }};
                    window.speechSynthesis.speak(ttsUtterance);
                    ttsState = 'playing';
                    btn.innerHTML = '&#9208;&#65039; Pause';
                    ttsKeepAlive = setInterval(function() {{
                        if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {{
                            window.speechSynthesis.pause();
                            window.speechSynthesis.resume();
                        }}
                    }}, 10000);
                }} else if (ttsState === 'playing') {{
                    window.speechSynthesis.pause();
                    ttsState = 'paused';
                    btn.innerHTML = '&#9654;&#65039; Resume';
                }} else if (ttsState === 'paused') {{
                    window.speechSynthesis.resume();
                    ttsState = 'playing';
                    btn.innerHTML = '&#9208;&#65039; Pause';
                }}
            }}
            function stopTTS() {{
                window.speechSynthesis.cancel();
                ttsState = 'stopped';
                document.getElementById('tts-play').innerHTML = '&#9654;&#65039; Play Audio';
                if (ttsKeepAlive) {{ clearInterval(ttsKeepAlive); ttsKeepAlive = null; }}
            }}
        </script>
        """, height=55)

        st.markdown(
            f"""<div style="
                font-size: 1.05rem;
                line-height: 1.85;
                padding: 1rem;
                background: #E8EAF6;
                border-radius: 12px;
                color: #1A237E;
            ">{lesson.audio_script}</div>""",
            unsafe_allow_html=True,
        )

    with tab_visual:
        cols = st.columns(min(len(lesson.visual_summary), 3))
        for i, point in enumerate(lesson.visual_summary):
            with cols[i % len(cols)]:
                st.markdown(
                    f"""<div style="
                        background: linear-gradient(135deg, #E1F5FE, #B3E5FC);
                        padding: 1.2rem;
                        border-radius: 12px;
                        text-align: center;
                        min-height: 100px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 1rem;
                        color: #01579B;
                        margin-bottom: 0.5rem;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    ">{point}</div>""",
                    unsafe_allow_html=True,
                )

    with tab_frames:
        if lesson.visual_frame_captions:
            st.caption("Timestamped captions from the video (Gemini).")
            for line in lesson.visual_frame_captions:
                st.markdown(
                    f"""<div style="
                        padding: 0.55rem 0.85rem;
                        margin: 0.35rem 0;
                        background: #F3E5F5;
                        border-radius: 8px;
                        border-left: 4px solid #8E24AA;
                        color: #4A148C;
                        font-size: 0.98rem;
                        line-height: 1.5;
                    ">{line}</div>""",
                    unsafe_allow_html=True,
                )
        else:
            st.info("Frame captions appear here after you process a **video** lesson.")


# ─────────────────────────────────────────────
# Accessibility Mode Section
# ─────────────────────────────────────────────
def render_accessibility_section(lesson: LessonData):
    """Render the accessibility mode selector and adapted content."""
    st.markdown('<div class="section-header">♿ Student Accessibility Modes</div>', unsafe_allow_html=True)

    st.markdown(
        '<div class="info-box">'
        "Select a learning mode below to view the lesson adapted for different accessibility needs."
        "</div>",
        unsafe_allow_html=True,
    )

    # Mode selector
    mode_keys = list(ACCESSIBILITY_MODES.keys())
    mode_labels = [ACCESSIBILITY_MODES[k]["label"] for k in mode_keys]

    cols = st.columns(len(mode_keys))
    for i, (key, info) in enumerate(ACCESSIBILITY_MODES.items()):
        with cols[i]:
            if st.button(
                info["label"],
                key=f"mode_btn_{key}",
                use_container_width=True,
            ):
                st.session_state["selected_mode"] = key

    # Render content for the selected mode
    selected = st.session_state.get("selected_mode", "dyslexia")
    st.divider()
    render_adapted_content(lesson, selected)


# ─────────────────────────────────────────────
# Quiz Section
# ─────────────────────────────────────────────
def render_quiz_section(lesson: LessonData):
    """Render the quiz and handle progress saving."""
    st.markdown('<div class="section-header">📝 Quiz & Assessment</div>', unsafe_allow_html=True)

    render_quiz(lesson)

    # Save progress if a new score was registered
    score = st.session_state.get("last_quiz_score")
    total = st.session_state.get("last_quiz_total")
    if score is not None and total is not None:
        mode = st.session_state.get("selected_mode", "standard")
        save_quiz_result(lesson.title, score, total, mode)
        # Reset so we don't save duplicates
        st.session_state["last_quiz_score"] = None
        st.session_state["last_quiz_total"] = None


# ─────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────
def main():
    inject_custom_css()
    init_session_state()

    # Sidebar
    input_mode = render_sidebar()

    # Hero
    render_hero()

    # --- Section 1: Lesson Input ---
    extracted_text, pdf_path, video_path = render_input_section(input_mode)

    # --- Section 2: AI Processing ---
    render_processing_section(extracted_text, pdf_path, video_path)

    # --- Sections 3-6: Only shown after processing ---
    lesson: LessonData | None = st.session_state.get("lesson_data")

    if lesson and st.session_state.get("processing_complete"):
        st.divider()

        # Section 3: AI-generated outputs
        render_lesson_output(lesson)

        st.divider()

        # Section 4: Accessibility modes
        render_accessibility_section(lesson)

        st.divider()

        # Section 5 & 6: Quiz + Adaptive feedback
        render_quiz_section(lesson)

    elif not st.session_state.get("processing_complete"):
        # Landing state
        st.divider()
        st.markdown("""
        <div style="
            text-align: center;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 100%);
            border-radius: 16px;
            margin: 1rem 0;
        ">
            <div style="font-size: 3rem; margin-bottom: 0.8rem;">📚</div>
            <h3 style="color: #333; margin: 0 0 0.5rem 0;">Get Started</h3>
            <p style="color: #666; font-size: 1.05rem; max-width: 500px; margin: 0 auto;">
                Choose <strong>Upload PDF</strong>, <strong>Paste Text</strong>, or <strong>Video</strong> in the sidebar, then click
                <strong>Process</strong> to generate accessible learning materials.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Feature cards
        st.markdown("")
        cols = st.columns(4)
        features = [
            ("🔤", "Dyslexia Support", "Simplified text with clear formatting"),
            ("👁️", "Visual Support", "Audio scripts for screen readers"),
            ("👂", "Hearing Support", "Rich text and visual summaries"),
            ("🐢", "Slow Learner", "Step-by-step chunked content"),
        ]
        for col, (icon, title, desc) in zip(cols, features):
            with col:
                st.markdown(
                    f"""<div style="
                        border: 1px solid #e0e0e0;
                        border-radius: 12px;
                        padding: 1.2rem;
                        text-align: center;
                        background: white;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                        transition: transform 0.2s ease;
                    ">
                        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
                        <div style="font-weight: 600; color: #333; margin-bottom: 0.3rem;">{title}</div>
                        <div style="font-size: 0.85rem; color: #888;">{desc}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )


if __name__ == "__main__":
    main()
