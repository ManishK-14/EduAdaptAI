"""
Quiz engine module.
Handles quiz rendering, answer collection, scoring, and adaptive feedback.
"""

import streamlit as st
from modules.lesson_parser import LessonData


def render_quiz(lesson: LessonData) -> None:
    """
    Render the interactive quiz section.
    Displays MCQ questions, collects answers, scores, and shows adaptive feedback.
    """
    quiz_questions = lesson.quiz

    if not quiz_questions:
        st.warning("No quiz questions were generated for this lesson.")
        return

    st.markdown("### 📝 Quiz — Test Your Understanding")
    st.caption(f"{len(quiz_questions)} questions • Select your answers and submit")
    st.divider()

    # Collect answers using a form for batch submission
    with st.form(key="quiz_form"):
        user_answers: dict[int, str] = {}

        for i, q in enumerate(quiz_questions):
            st.markdown(
                f"""<div style="
                    background: #F5F5F5;
                    padding: 0.8rem 1rem;
                    border-radius: 10px;
                    margin-bottom: 0.3rem;
                    font-size: 1.05rem;
                    font-weight: 500;
                    color: #212121;
                "><strong>Q{i+1}.</strong> {q['question']}</div>""",
                unsafe_allow_html=True,
            )

            user_answers[i] = st.radio(
                label=f"Select answer for Q{i+1}",
                options=q["options"],
                key=f"quiz_q_{i}",
                label_visibility="collapsed",
            )

            if i < len(quiz_questions) - 1:
                st.markdown("<br>", unsafe_allow_html=True)

        submitted = st.form_submit_button(
            "✅ Submit Quiz",
            use_container_width=True,
            type="primary",
        )

    # Process results after submission
    if submitted:
        score = _calculate_score(quiz_questions, user_answers)
        _display_results(score, len(quiz_questions), quiz_questions, user_answers)
        _display_adaptive_feedback(score, lesson)

        # Store score in session state for progress tracking
        st.session_state["last_quiz_score"] = score
        st.session_state["last_quiz_total"] = len(quiz_questions)


def score_quiz_submission(quiz_questions: list[dict], answers: list[str]) -> dict:
    """
    Score a quiz from plain lists (API / non-Streamlit callers).
    answers[i] must be the selected option string for question i (same as q["answer"] when correct).
    """
    total = len(quiz_questions)
    if total == 0:
        return {
            "score": 0,
            "total": 0,
            "percentage": 0.0,
            "details": [],
        }
    correct = 0
    details: list[dict] = []
    for i, q in enumerate(quiz_questions):
        user_ans = answers[i] if i < len(answers) else None
        expected = q.get("answer")
        is_correct = user_ans == expected
        if is_correct:
            correct += 1
        details.append({
            "question_index": i,
            "correct": is_correct,
            "correct_answer": expected,
            "selected": user_ans,
        })
    return {
        "score": correct,
        "total": total,
        "percentage": round((correct / total) * 100, 1),
        "details": details,
    }


def _calculate_score(
    questions: list[dict], user_answers: dict[int, str]
) -> int:
    """Calculate the number of correct answers."""
    correct = 0
    for i, q in enumerate(questions):
        if user_answers.get(i) == q["answer"]:
            correct += 1
    return correct


def _display_results(
    score: int,
    total: int,
    questions: list[dict],
    user_answers: dict[int, str],
) -> None:
    """Display score and per-question results."""
    percentage = (score / total) * 100 if total > 0 else 0

    # Score banner
    if percentage >= 80:
        color, emoji = "#4CAF50", "🎉"
    elif percentage >= 50:
        color, emoji = "#FF9800", "👍"
    else:
        color, emoji = "#F44336", "💪"

    st.markdown(
        f"""<div style="
            background: {color};
            color: white;
            padding: 1.2rem;
            border-radius: 12px;
            text-align: center;
            font-size: 1.3rem;
            margin: 1rem 0;
        ">{emoji} You scored <strong>{score}/{total}</strong> ({percentage:.0f}%)</div>""",
        unsafe_allow_html=True,
    )

    # Detailed results
    with st.expander("📋 View Detailed Results", expanded=True):
        for i, q in enumerate(questions):
            user_ans = user_answers.get(i, "")
            is_correct = user_ans == q["answer"]

            if is_correct:
                st.markdown(f"**Q{i+1}.** {q['question']}")
                st.success(f"✅ Your answer: {user_ans}")
            else:
                st.markdown(f"**Q{i+1}.** {q['question']}")
                st.error(f"❌ Your answer: {user_ans}")
                st.info(f"✔️ Correct answer: {q['answer']}")

            if i < len(questions) - 1:
                st.markdown("---")


def _display_adaptive_feedback(score: int, lesson: LessonData) -> None:
    """
    Show adaptive feedback based on quiz score.
    - score <= 2 → needs easier explanation
    - score >= 4 → great progress, show key concepts as challenge revision
    - otherwise  → good understanding
    """
    st.markdown("### 🎯 Adaptive Feedback")

    if score <= 2:
        st.error("🔄 **Looks like you need more practice.** Let's review the simplified explanation again.")
        st.markdown(
            f"""<div style="
                background: #FFEBEE;
                padding: 1.2rem;
                border-radius: 12px;
                font-size: 1.05rem;
                line-height: 1.9;
                border-left: 5px solid #F44336;
                color: #B71C1C;
            ">{lesson.simplified_explanation}</div>""",
            unsafe_allow_html=True,
        )
        st.info("💡 **Tip:** Try reading the simplified explanation slowly, then retake the quiz.")

    elif score >= 4:
        st.success("🌟 **Great progress!** You've demonstrated strong understanding.")
        st.markdown("**🚀 Challenge yourself — review these key concepts:**")
        for i, concept in enumerate(lesson.key_concepts, 1):
            st.markdown(
                f"""<div style="
                    background: #E8F5E9;
                    padding: 0.7rem 1rem;
                    border-radius: 8px;
                    margin: 0.3rem 0;
                    border-left: 4px solid #4CAF50;
                    color: #1B5E20;
                "><strong>{i}.</strong> {concept}</div>""",
                unsafe_allow_html=True,
            )
        st.balloons()

    else:
        st.warning("👍 **Good understanding!** A little more review will help solidify the concepts.")
        st.markdown("**📚 Suggested next steps:**")
        st.markdown("- Re-read the lesson summary")
        st.markdown("- Focus on concepts you missed in the quiz")
        st.markdown("- Try an accessibility mode that suits your learning style")
