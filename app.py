import base64
import io
import os

import requests
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from pypdf import PdfReader

OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
MODEL = os.getenv("CHAT_MODEL", "gemma4:e2b")   # the ONLY model used
MAX_CHARS = 60000                               # keep notes within Gemma 4's long context
MAX_IMAGES = 3

app = FastAPI(title="Study Buddy (Gemma 4 only)")
notes = []    # [{"name": str, "text": str}]
images = []   # [{"name": str, "b64": str}]

IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp")


@app.get("/")
def home():
    return FileResponse("index.html")


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    data = await file.read()
    name = file.filename or "notes"
    lower = name.lower()

    if lower.endswith(IMAGE_EXT):
        images.append({"name": name, "b64": base64.b64encode(data).decode()})
        del images[:-MAX_IMAGES]   # keep only the latest few photos
        return {"file": name, "kind": "image"}

    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
    else:
        text = data.decode("utf-8", errors="ignore")

    text = " ".join(text.split())
    if not text:
        return JSONResponse({"error": "No readable text found in this file."}, status_code=400)
    notes.append({"name": name, "text": text})
    return {"file": name, "kind": "text", "characters": len(text)}


class Ask(BaseModel):
    question: str
    mode: str = "answer"      # answer | summary | quiz
    language: str = "auto"


@app.post("/ask")
def ask(body: Ask):
    if not notes and not images:
        return {"answer": "Pehle apne notes ya notes ki photo upload karo."}

    all_text = "\n\n".join(f"[{n['name']}]\n{n['text']}" for n in notes)[:MAX_CHARS]

    if body.language == "auto":
        lang_rule = (
            "Reply in the same language the student used. If the student writes Hindi "
            "in Roman letters (Hinglish), reply in Hinglish."
        )
    else:
        lang_rule = f"Reply in {body.language}."

    tasks = {
        "answer": "Answer the student's question clearly and simply, with a short example if useful.",
        "summary": "Summarize the notes about the topic in simple bullet points.",
        "quiz": "Create 5 multiple-choice questions (4 options each) from the notes. "
                "Put all correct answers at the end.",
    }
    system = (
        "You are a friendly study buddy for students. Use ONLY the notes provided "
        "(text and any attached photos of notes). If the notes do not contain the answer, "
        f"say so honestly instead of guessing. {tasks.get(body.mode, tasks['answer'])} {lang_rule}"
    )
    user = f"NOTES:\n{all_text or '(see attached photos)'}\n\nSTUDENT:\n{body.question}"
    message = {"role": "user", "content": user}
    if images:
        message["images"] = [i["b64"] for i in images]

    try:
        r = requests.post(
            f"{OLLAMA}/api/chat",
            json={
                "model": MODEL,
                "stream": False,
                "messages": [{"role": "system", "content": system}, message],
            },
            timeout=900,
        )
        r.raise_for_status()
    except requests.RequestException as e:
        return JSONResponse(
            {"error": f"Ollama error: {e}. Is Ollama running and {MODEL} pulled?"},
            status_code=500,
        )
    return {"answer": r.json()["message"]["content"]}


@app.post("/reset")
def reset():
    notes.clear()
    images.clear()
    return {"status": "cleared"}