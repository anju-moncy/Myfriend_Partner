from openai import OpenAI
from datetime import datetime
from database import get_chat_history, add_chat, add_reminder, get_or_create_user
from sqlalchemy.orm import Session
import re
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()  # Uses OPENAI_API_KEY from environment


def chat_with_llm(user_text: str, mood: str, session_id: str, db: Session):
    user = get_or_create_user(session_id, db)
    history = get_chat_history(user.id, db)

    # Build messages with history for memory
    messages = [
        {
            "role": "system",
            "content": f"You are a true friend AI named 'Friend'. Be empathetic, supportive, and caring. Remember past chats to build a relationship. Current user mood: {mood}. If the user mentions check-ins or reminders, offer to set them up. Suggest gentle check-ins if they seem down. Keep responses warm and concise (under 150 words).",
        }
    ]

    # Add history (last 5 exchanges for token efficiency)
    for chat in history[-5:]:
        messages.append({"role": "user", "content": chat.user_message})
        messages.append({"role": "assistant", "content": chat.ai_response})

    messages.append({"role": "user", "content": user_text})

    # Generate response
    response = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, max_tokens=150
    )
    reply_text = response.choices[0].message.content

    # Detect and handle reminders (simple regex + LLM parse; improve with full LLM extraction)
    if "remind me" in user_text.lower() or "reminder" in user_text.lower():
        # Extract time/message (basic; use LLM for complex parsing)
        time_match = re.search(r"at (\d{1,2}:\d{2} (AM|PM)?)", user_text, re.IGNORECASE)
        if time_match:
            # Parse time (simplified; use dateutil for robustness)
            reminder_time = datetime.now().replace(
                hour=int(time_match.group(1).split(":")[0]),
                minute=int(time_match.group(1).split(":")[1]),
            )
            reminder_msg = (
                user_text.split("to ")[1] if "to " in user_text else "Your reminder"
            )
            add_reminder(user.id, reminder_msg, reminder_time, db)
            reply_text += f"\n\nGot it! I'll remind you about '{reminder_msg}' at {time_match.group(1)}."

    # Suggest check-in if mood is negative
    if mood in ["sadness", "anger", "fear"]:
        reply_text += "\n\nHow about we check in tomorrow? I'm here anytime."

    # Save to DB
    add_chat(user.id, user_text, reply_text, mood, db)

    return reply_text
