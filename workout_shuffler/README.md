# AI Workout Shuffler

A Flask web app that uses Google Gemini AI to intelligently reorder workout plans and suggest new exercises.

## Setup

### 1. Clone / navigate to the project
```bash
cd workout_shuffler
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Add your Gemini API key
Edit `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_actual_key_here
```
Get a free key at https://aistudio.google.com/app/apikey

### 5. Run the app
```bash
python app.py
```

Open http://localhost:5000 in your browser.

## Features

- **AI Shuffle** — Gemini reorders exercises to minimise muscle fatigue based on your history
- **Random Shuffle** — instant shuffle with no API call; always works as a fallback
- **AI Suggestions** — Gemini proposes 4 complementary exercises with reasoning; add them directly to your plan
- **Session History** — every shuffle is logged; browse by plan or view all
- **Seed data** — two starter plans (Leg Day, Push Day) are created automatically on first run

## Notes

- If the Gemini API fails (bad key, quota, etc.) AI Shuffle automatically falls back to Random Shuffle with a warning message.
- The SQLite database file (`workouts.db`) is created automatically next to `app.py` on first run.
- To use a different Gemini model (e.g. `gemini-2.0-flash`), edit the `GenerativeModel` call in `services/ai_shuffler.py` and `services/ai_suggester.py`.
