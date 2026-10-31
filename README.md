# Multilingual Study Buddy

An offline AI study assistant powered by Gemma 4. Upload your notes (PDF, text or a photo) and ask questions in Hindi, Hinglish, English or other languages. It can answer, summarize a topic, or quiz you.

Built for Hacktoberfest 2026.

## Features

- Upload notes as PDF, text or image
- Three modes: answer, summarize, quiz
- Reply in the same language as the question, or a language you choose
- Answers only from your notes, and says so when the answer is not there
- Runs locally through Ollama, so notes stay on your machine

## How it works

Browser (HTML, CSS, JavaScript) -> FastAPI -> Gemma 4 through Ollama

Notes are passed directly to Gemma 4 using its long context window. No separate embedding model or vector database is needed.

## Setup

1. Install Python 3.12, Git and Ollama.
2. Download the model:

    ollama pull gemma4:e2b

3. Create a virtual environment and install packages:

    py -3.12 -m venv .venv
    .\.venv\Scripts\Activate.ps1
    python -m pip install -r requirements.txt

4. Run the app:

    uvicorn app:app --reload

5. Open http://127.0.0.1:8000

To use another model, set the CHAT_MODEL environment variable.

## Tech stack

Gemma 4 (gemma4:e2b), Ollama, FastAPI, Python, HTML, CSS, JavaScript, pypdf

## Author

Ansh Yadav