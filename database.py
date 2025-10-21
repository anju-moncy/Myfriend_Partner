import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from typing import Generator, List, Optional
from sqlalchemy.orm import Session
import logging

# Logging (for consistency)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup (SQLite for local; change for prod)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}  # SQLite fix
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, default="Anonymous")
    email = Column(String, unique=True, index=True, nullable=True)
    session_id = Column(String, unique=True, index=True)
    last_mood = Column(String, default="neutral")
    last_activity = Column(DateTime, default=datetime.now)
    reminders = relationship("Reminder", back_populates="user")


class Reminder(Base):
    __tablename__ = "reminders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    scheduled_time = Column(DateTime)
    sent = Column(Boolean, default=False)
    user = relationship("User", back_populates="reminders")


# Chat history for memory
class Chat(Base):
    __tablename__ = "chats"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    user_message = Column(String)
    ai_response = Column(String)
    mood = Column(String, default="neutral")
    created_at = Column(DateTime, default=datetime.now)


# Create tables
Base.metadata.create_all(bind=engine)


# DB Dependency (for FastAPI)
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Missing Functions (these resolve the errors)
def get_pending_reminders(db: Session) -> List[Reminder]:
    """Fetch unsent reminders due now or earlier."""
    now = datetime.now()
    return (
        db.query(Reminder)
        .filter(Reminder.sent == False, Reminder.scheduled_time <= now)
        .all()
    )


def mark_reminder_sent(reminder_id: int, db: Session) -> bool:
    """Mark a reminder as sent."""
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if reminder:
        reminder.sent = True
        db.commit()
        return True
    logger.warning(f"Reminder {reminder_id} not found")
    return False


# Additional: get_or_create_user (from previous; for /chat endpoint)
def get_or_create_user(session_id: str, db: Session) -> User:
    """Fetch or create user by session_id."""
    user = db.query(User).filter(User.session_id == session_id).first()
    if not user:
        user = User(session_id=session_id, name="Anonymous User")
        db.add(user)
        db.commit()
        logger.info(f"Created user for session: {session_id}")
    return user


# New helpers used by llm.py
def add_chat(
    user_id: int,
    user_message: str,
    ai_response: str,
    mood: str,
    db: Session,
) -> Chat:
    chat = Chat(
        user_id=user_id,
        user_message=user_message,
        ai_response=ai_response,
        mood=mood,
    )
    db.add(chat)
    db.commit()
    db.refresh(chat)
    return chat


def get_chat_history(user_id: int, db: Session) -> List[Chat]:
    return db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.id.asc()).all()


def add_reminder(user_id: int, message: str, when: datetime, db: Session) -> Reminder:
    reminder = Reminder(user_id=user_id, message=message, scheduled_time=when)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


# Test (run python database.py to verify)
if __name__ == "__main__":
    db = next(get_db())
    try:
        print("DB setup OK. Tables created.")
    finally:
        db.close()
