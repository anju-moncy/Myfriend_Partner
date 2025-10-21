from fastapi import FastAPI, UploadFile, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

import uuid
import asyncio
import os
import logging
import atexit

from stt import transcribe_audio
from emotion import detect_emotion
from llm import chat_with_llm
from tts import synthesize_speech
from database import (
    User,
    get_db,
    get_or_create_user,
    get_pending_reminders,
    mark_reminder_sent,
)

app = FastAPI(title="Friend AI - Your True Friend")

# Allow Streamlit (localhost:8501) to call the API during local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Temp audio dir
os.makedirs("temp_audio", exist_ok=True)

# Scheduler for reminders and check-ins (runs in background)
scheduler = BackgroundScheduler()


def handle_reminders():
    db = next(get_db())
    reminders = get_pending_reminders(db)
    for rem in reminders:
        logger.info(f"Reminder for user {rem.user_id}: {rem.message}")
        # Extend: Send email/SMS here (e.g., via smtplib or Twilio)
        mark_reminder_sent(rem.id, db)
    db.close()


def proactive_checkin():
    db = next(get_db())
    users = db.query(User).all()
    for user in users:
        logger.info(
            f"Proactive check-in for user {user.id} "
            f"(session: {user.session_id}) - How are you today?"
        )
        # Extend: Send notification if last chat >24h
    db.close()


@app.on_event("startup")
def start_scheduler() -> None:
    """Start APScheduler and register jobs on app startup."""
    if not scheduler.running:
        scheduler.add_job(
            handle_reminders,
            "interval",
            minutes=1,
            id="handle_reminders",
            replace_existing=True,
        )
        scheduler.add_job(
            proactive_checkin,
            "interval",
            hours=24,
            id="proactive_checkin",
            replace_existing=True,
        )
        scheduler.start()


@app.post("/chat")
async def chat(
    file: UploadFile,
    session_id: str = Query(..., description="User session ID (UUID)"),
    db: Session = Depends(get_db),
):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")

    user = get_or_create_user(session_id, db)
    audio_filename = os.path.join("temp_audio", f"reply_{uuid.uuid4().hex}.wav")

    # 1. STT
    try:
        text = await transcribe_audio(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STT error: {e}")

    # 2. Emotion
    mood = detect_emotion(text)

    # 3. LLM with memory
    try:
        reply_text = await asyncio.to_thread(chat_with_llm, text, mood, session_id, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM error: {e}")

    # 4. TTS
    try:
        audio_path = await asyncio.to_thread(
            synthesize_speech, reply_text, audio_filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS error: {e}")

    return {
        "user_id": user.id,
        "session_id": session_id,
        "transcript": text,
        "mood": mood,
        "reply": reply_text,
        "audio": os.path.basename(audio_path),
    }


@app.post("/checkin")
async def checkin(
    session_id: str,
    message: str = "How are you feeling today?",
    db: Session = Depends(get_db),
):
    user = get_or_create_user(session_id, db)
    mood = detect_emotion(message)
    reply_text = await asyncio.to_thread(chat_with_llm, message, mood, session_id, db)
    return {"user_id": user.id, "mood": mood, "friend_response": reply_text}


@app.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join("temp_audio", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="File not found")


@app.on_event("shutdown")
def shutdown_scheduler() -> None:
    """Cleanly shut down the scheduler on app shutdown."""
    if scheduler.running:
        scheduler.shutdown()
