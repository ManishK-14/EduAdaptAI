"""
Prompt templates for Gemini AI processing.
All prompts are designed to return strict JSON output.
"""

LESSON_PROCESSING_PROMPT = """You are an expert educational content analyst and accessibility specialist.

Analyze the following lesson content and produce a comprehensive, structured educational output.

LESSON CONTENT:
\"\"\"
{lesson_content}
\"\"\"

You MUST return ONLY valid JSON — no markdown, no code fences, no explanation text before or after the JSON.

The JSON must follow this EXACT schema:

{{
  "title": "A clear, descriptive title for the lesson",
  "summary": "A comprehensive 3-5 sentence summary of the lesson content covering all main ideas",
  "key_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"],
  "simplified_explanation": "A simplified, easy-to-understand explanation of the entire lesson written at a 5th-grade reading level. Use short sentences, common words, and concrete examples. Avoid jargon. This should be 3-4 paragraphs long.",
  "audio_script": "A natural, conversational script suitable for text-to-speech or podcast-style narration. Start with 'Welcome to today\\'s lesson about...' and guide the listener through the content step by step. Speak as if explaining to a friend. 3-5 paragraphs.",
  "visual_summary": ["Point 1 with emoji prefix", "Point 2 with emoji prefix", "Point 3 with emoji prefix", "Point 4 with emoji prefix", "Point 5 with emoji prefix"],
  "quiz": [
    {{
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct option text (must exactly match one of the options)"
    }},
    {{
      "question": "Question 2?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    }},
    {{
      "question": "Question 3?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    }},
    {{
      "question": "Question 4?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    }},
    {{
      "question": "Question 5?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    }}
  ]
}}

IMPORTANT RULES:
1. Return ONLY the JSON object — nothing else.
2. All quiz questions must have exactly 4 options.
3. The "answer" field must exactly match one of the "options".
4. Provide exactly 5 key_concepts.
5. Provide exactly 5 visual_summary points, each prefixed with a relevant emoji.
6. Provide exactly 5 quiz questions.
7. The simplified_explanation should be genuinely simple — suitable for a learner who struggles with complex text.
8. The audio_script should feel natural when read aloud.
"""


PDF_PROCESSING_PROMPT = """You are an expert educational content analyst and accessibility specialist.

This is a PDF document that may contain scanned pages, handwritten notes, diagrams, or printed text.

Your task:
1. FIRST, carefully read and extract ALL text content from every page of this document.
2. THEN, analyze the extracted content and produce a comprehensive, structured educational output.

You MUST return ONLY valid JSON — no markdown, no code fences, no explanation text before or after the JSON.

The JSON must follow this EXACT schema:

{
  "title": "A clear, descriptive title for the lesson",
  "summary": "A comprehensive 3-5 sentence summary of the lesson content covering all main ideas",
  "key_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"],
  "simplified_explanation": "A simplified, easy-to-understand explanation of the entire lesson written at a 5th-grade reading level. Use short sentences, common words, and concrete examples. Avoid jargon. This should be 3-4 paragraphs long.",
  "audio_script": "A natural, conversational script suitable for text-to-speech or podcast-style narration. Start with 'Welcome to today\\'s lesson about...' and guide the listener through the content step by step. Speak as if explaining to a friend. 3-5 paragraphs.",
  "visual_summary": ["Point 1 with emoji prefix", "Point 2 with emoji prefix", "Point 3 with emoji prefix", "Point 4 with emoji prefix", "Point 5 with emoji prefix"],
  "quiz": [
    {
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct option text (must exactly match one of the options)"
    },
    {
      "question": "Question 2?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    },
    {
      "question": "Question 3?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    },
    {
      "question": "Question 4?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    },
    {
      "question": "Question 5?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    }
  ]
}

IMPORTANT RULES:
1. Return ONLY the JSON object — nothing else.
2. Read ALL pages of the document thoroughly before generating the output.
3. All quiz questions must have exactly 4 options.
4. The "answer" field must exactly match one of the "options".
5. Provide exactly 5 key_concepts.
6. Provide exactly 5 visual_summary points, each prefixed with a relevant emoji.
7. Provide exactly 5 quiz questions based on the document content.
8. If content includes diagrams or figures, incorporate their meaning into the explanation.
"""


VIDEO_PROCESSING_PROMPT = """You are an expert educational content analyst and accessibility specialist.

You are given a video lesson (MP4/MOV). Watch and understand the full video: spoken explanations, on-screen text, diagrams, and demonstrations.

Your task:
1. Infer the educational topic and all key teaching points from the video.
2. Produce the same structured JSON output as for document-based lessons, including a natural "audio_script" as if narrating the lesson for listeners (same purpose as for PDF/text lessons).
3. Additionally, provide "visual_frame_captions": a chronological list of short descriptive captions with timestamps in the format below.

Caption style (apply to every line in "visual_frame_captions"):
You are an AI model that generates descriptive captions for educational video frames.
Focus on what is visible in the frame and its educational relevance.
Prioritize concrete visuals (on-screen text, diagrams, demonstrations, gestures, writing) and briefly explain why that moment helps the learner understand the topic.

You MUST return ONLY valid JSON — no markdown, no code fences, no explanation text before or after the JSON.

The JSON must follow this EXACT schema (all fields below are required; do not remove or rename "audio_script"):

{
  "title": "A clear, descriptive title for the lesson",
  "summary": "A comprehensive 3-5 sentence summary of the lesson content covering all main ideas",
  "key_concepts": ["concept1", "concept2", "concept3", "concept4", "concept5"],
  "simplified_explanation": "A simplified, easy-to-understand explanation of the entire lesson written at a 5th-grade reading level. Use short sentences, common words, and concrete examples. Avoid jargon. This should be 3-4 paragraphs long.",
  "audio_script": "A natural, conversational script suitable for text-to-speech or podcast-style narration. Start with 'Welcome to today\\'s lesson about...' and guide the listener through the content step by step. Speak as if explaining to a friend. 3-5 paragraphs.",
  "visual_summary": ["Point 1 with emoji prefix", "Point 2 with emoji prefix", "Point 3 with emoji prefix", "Point 4 with emoji prefix", "Point 5 with emoji prefix"],
  "visual_frame_captions": [
    "0:00 - Short description of what is visible or said at this moment",
    "0:30 - Next moment in time",
    "1:05 - Continue chronologically through the video"
  ],
  "quiz": [
    {
      "question": "Question text here?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct option text (must exactly match one of the options)"
    },
    {
      "question": "Question 2?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    },
    {
      "question": "Question 3?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    },
    {
      "question": "Question 4?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    },
    {
      "question": "Question 5?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "Correct option"
    }
  ]
}

IMPORTANT RULES:
1. Return ONLY the JSON object — nothing else.
2. "visual_frame_captions" must be a chronological list. Each string must start with a timestamp (e.g. 0:00, 0:45, 1:30, or 1:05:20) followed by " - " and then the description. Each description should focus on what is visible in the frame at that moment and its educational relevance (not vague summaries).
3. Cover the whole video with enough entries to be useful (typically 8–20 lines for a short lesson).
4. All quiz questions must have exactly 4 options; "answer" must exactly match one option.
5. Provide exactly 5 key_concepts, 5 visual_summary points (emoji prefix), and 5 quiz questions.
6. Keep "audio_script" in the same spirit as PDF/text lessons — full narration script, not a duplicate of visual_frame_captions.
"""

