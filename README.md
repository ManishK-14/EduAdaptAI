# 🎓 EduAdapt AI — Inclusive Learning Platform

> **Teach once. Adapt for every learner.**

An AI-powered inclusive learning platform that transforms any lesson into multiple accessible formats using Google Gemini AI. Upload a PDF or paste text, and the system automatically generates summaries, simplified explanations, audio scripts, visual summaries, and quizzes — all adapted for different learning needs.

---

## ✨ Features

- **📄 Multi-format Input** — Upload PDF files or paste lesson text directly
- **🤖 Gemini AI Processing** — Powered by Gemini 1.5 Flash for fast, structured output
- **♿ 4 Accessibility Modes:**
  - 🔤 **Dyslexia Support** — Simplified language + bullet-point concepts
  - 👁️ **Visual Support** — Audio-friendly scripts + structured content
  - 👂 **Hearing Support** — Text summaries + visual points
  - 🐢 **Slow Learner Support** — Chunked content, one concept at a time
- **📝 Interactive Quiz** — 5 MCQ questions with instant scoring
- **🎯 Adaptive Feedback** — Personalized response based on quiz performance
- **📊 Progress Tracking** — Local JSON-based score history

---

## 🚀 Quick Start

### 1. Clone / Download the Project

```bash
cd inclusive-learning-ai
```

### 2. Create a Virtual Environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Your Gemini API Key

1. Get a free API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a `.env` file in the project root:

```bash
copy .env.example .env
```

3. Open `.env` and replace `your_gemini_api_key_here` with your actual key:

```
GEMINI_API_KEY=AIzaSy...your_actual_key_here
```

### 5. Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

---

## 📁 Project Structure

```
inclusive-learning-ai/
│
├── app.py                       # Main Streamlit application
├── .env                         # Your API key (create from .env.example)
├── .env.example                 # Template for environment variables
├── requirements.txt             # Python dependencies
├── README.md                    # This file
│
├── modules/
│   ├── file_processor.py        # PDF/text upload & extraction
│   ├── gemini_service.py        # Gemini API communication
│   ├── lesson_parser.py         # Parse & structure AI output
│   ├── adaptation_engine.py     # Accessibility mode rendering
│   ├── quiz_engine.py           # Quiz display, scoring, feedback
│   └── progress_tracker.py      # Local progress storage
│
├── data/
│   ├── uploads/                 # Uploaded files (auto-created)
│   └── student_progress.json    # Quiz score history
│
└── utils/
    ├── prompts.py               # Gemini prompt templates
    └── helpers.py               # JSON parsing, validation, utilities
```

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.10+ | Core language |
| Streamlit | Web UI framework |
| google-generativeai | Gemini API SDK |
| pdfplumber | PDF text extraction |
| python-dotenv | Environment variable management |

---

## 🐛 Common Issues & Fixes

### "Gemini API key not configured"
- Make sure you have a `.env` file with `GEMINI_API_KEY=your_key`
- The key must **not** be in quotes

### "Could not extract text from PDF"
- The PDF might be image-based (scanned). This app requires text-based PDFs.
- Try copying text from the PDF manually and using "Paste Text" mode.

### "Could not parse JSON from Gemini response"
- The app has built-in retry logic. Try clicking "Process" again.
- If it persists, try with shorter or simpler content.

### Module import errors
- Make sure you're running `streamlit run app.py` from the `inclusive-learning-ai/` directory
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### Streamlit version issues
- Requires Streamlit 1.30.0 or higher: `pip install --upgrade streamlit`

---

## 📜 License

MIT License — Free for educational and hackathon use.

---

Built with ❤️ for inclusive education | Powered by Google Gemini AI
