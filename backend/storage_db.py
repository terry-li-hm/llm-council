"""PostgreSQL-based storage for conversations (used when DATABASE_URL is set)."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

# SQLAlchemy setup
Base = declarative_base()
engine = None
SessionLocal = None


class Conversation(Base):
    """Conversation model for PostgreSQL storage."""
    __tablename__ = "conversations"

    id = Column(String(255), primary_key=True)
    title = Column(String(500), default="New Conversation")
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = Column(Text, default="[]")  # JSON-encoded messages


def init_db():
    """Initialize database connection and create tables."""
    global engine, SessionLocal
    if DATABASE_URL:
        # Railway uses postgres:// but SQLAlchemy needs postgresql://
        db_url = DATABASE_URL
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)

        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    if SessionLocal is None:
        init_db()
    return SessionLocal()


def create_conversation(conversation_id: str) -> Dict[str, Any]:
    """Create a new conversation."""
    session = get_session()
    try:
        conv = Conversation(
            id=conversation_id,
            title="New Conversation",
            created_at=datetime.utcnow(),
            messages="[]"
        )
        session.add(conv)
        session.commit()

        return {
            "id": conv.id,
            "created_at": conv.created_at.isoformat(),
            "title": conv.title,
            "messages": []
        }
    finally:
        session.close()


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load a conversation from database."""
    session = get_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation_id).first()
        if conv is None:
            return None

        return {
            "id": conv.id,
            "created_at": conv.created_at.isoformat(),
            "title": conv.title,
            "messages": json.loads(conv.messages)
        }
    finally:
        session.close()


def save_conversation(conversation: Dict[str, Any]):
    """Save a conversation to database."""
    session = get_session()
    try:
        conv = session.query(Conversation).filter_by(id=conversation['id']).first()
        if conv is None:
            conv = Conversation(id=conversation['id'])
            session.add(conv)

        conv.title = conversation.get('title', 'New Conversation')
        conv.messages = json.dumps(conversation.get('messages', []))

        session.commit()
    finally:
        session.close()


def list_conversations() -> List[Dict[str, Any]]:
    """List all conversations (metadata only)."""
    session = get_session()
    try:
        convs = session.query(Conversation).order_by(Conversation.created_at.desc()).all()

        return [
            {
                "id": conv.id,
                "created_at": conv.created_at.isoformat(),
                "title": conv.title,
                "message_count": len(json.loads(conv.messages))
            }
            for conv in convs
        ]
    finally:
        session.close()


def add_user_message(conversation_id: str, content: str):
    """Add a user message to a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "user",
        "content": content
    })

    save_conversation(conversation)


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
):
    """Add an assistant message with all 3 stages to a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    })

    save_conversation(conversation)


def update_conversation_title(conversation_id: str, title: str):
    """Update the title of a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["title"] = title
    save_conversation(conversation)


def add_followup_message(conversation_id: str, response: Dict[str, Any]):
    """Add a chairman follow-up response to a conversation."""
    conversation = get_conversation(conversation_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "assistant",
        "type": "followup",
        "response": response
    })

    save_conversation(conversation)
