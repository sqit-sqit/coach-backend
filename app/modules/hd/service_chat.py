# app/modules/hd/service_chat.py
import os
import yaml
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import ChatSession, ChatMessage
from app.core.chat_service import BaseChatService
from app.config.ai_models import get_model_config
from app.modules.hd.models import HDSession, HDChatMessage

# załaduj zmienne z .env
load_dotenv()


class HDChatService(BaseChatService):
    """
    Specjalizowany serwis chat dla Human Design.
    Dziedziczy z BaseChatService i implementuje specyficzną logikę HD.
    """
    
    def __init__(self):
        super().__init__("hd")
    
    def _get_start_message(self) -> str:
        """Wiadomość startowa dla HD chat."""
        return "Start the Human Design conversation. Begin with an introduction about my chart."
    
    def _load_personality(self, context_data: dict) -> str:
        """Ładuje personality HD z danymi użytkownika."""
        return load_hd_personality(context_data)
    
    def _save_user_message(self, user_message: str, user_id: str, context_data: dict):
        """Zapisuje wiadomość użytkownika do bazy HD."""
        db = next(get_db())
        try:
            # Znajdź sesję HD
            hd_session = db.query(HDSession).filter(
                HDSession.user_id == user_id
            ).order_by(HDSession.started_at.desc()).first()
            
            if hd_session:
                # Znajdź ostatni message_order
                last_message = db.query(HDChatMessage).filter(
                    HDChatMessage.session_id == hd_session.session_id
                ).order_by(HDChatMessage.message_order.desc()).first()
                
                next_order = (last_message.message_order + 1) if last_message else 1
                
                # Zapisz wiadomość użytkownika
                user_msg = HDChatMessage(
                    session_id=hd_session.session_id,
                    role="user",
                    content=user_message,
                    message_order=next_order
                )
                db.add(user_msg)
                db.commit()
        finally:
            db.close()
    
    def _save_ai_message(self, ai_response: str, user_id: str, context_data: dict):
        """Zapisuje odpowiedź AI do bazy HD."""
        db = next(get_db())
        try:
            # Znajdź sesję HD
            hd_session = db.query(HDSession).filter(
                HDSession.user_id == user_id
            ).order_by(HDSession.started_at.desc()).first()
            
            if hd_session:
                # Znajdź ostatni message_order
                last_message = db.query(HDChatMessage).filter(
                    HDChatMessage.session_id == hd_session.session_id
                ).order_by(HDChatMessage.message_order.desc()).first()
                
                next_order = (last_message.message_order + 1) if last_message else 1
                
                # Zapisz odpowiedź AI
                ai_msg = HDChatMessage(
                    session_id=hd_session.session_id,
                    role="assistant",
                    content=ai_response,
                    message_order=next_order
                )
                db.add(ai_msg)
                db.commit()
        finally:
            db.close()


# 🔹 Wczytywanie pliku osobowości HD
def load_hd_personality(hd_data: dict) -> str:
    """
    Ładuje osobowość HD z pliku i podstawia dane użytkownika.
    """
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    file_path = base_dir / "hd_personality_chat.txt"

    if not file_path.exists():
        return "You are a helpful Human Design AI assistant."

    raw = file_path.read_text(encoding="utf-8")
    
    # Podstaw dane HD
    return (raw
        .replace("{type}", hd_data.get("type", "Unknown"))
        .replace("{strategy}", hd_data.get("strategy", "Unknown"))
        .replace("{authority}", hd_data.get("authority", "Unknown"))
        .replace("{profile}", hd_data.get("profile", "Unknown"))
        .replace("{name}", hd_data.get("name", "Guest"))
        .replace("{birth_place}", hd_data.get("birth_place", "Unknown"))
        .replace("{birth_date}", hd_data.get("birth_date", "Unknown"))
        .replace("{birth_time}", hd_data.get("birth_time", "Unknown"))
        .replace("{active_gates}", str(hd_data.get("active_gates", [])))
        .replace("{defined_centers}", str(hd_data.get("defined_centers", [])))
        .replace("{undefined_centers}", str(hd_data.get("undefined_centers", [])))
        .replace("{defined_channels}", str(hd_data.get("defined_channels", [])))
        .replace("{activations}", str(hd_data.get("activations", [])))
    )

# 🔹 Główna funkcja czatu HD (legacy - używa HDChatService)
def chat_with_hd_ai(user_message: str, history: list[dict] = None, hd_data: dict = None, user_id: str = None) -> str:
    """
    Tworzy odpowiedź AI bazując na danych HD użytkownika.
    Używa HDChatService do zachowania kompatybilności wstecznej.
    """
    if history is None:
        history = []
    if hd_data is None:
        hd_data = {}

    # Użyj HDChatService do generowania odpowiedzi
    service = HDChatService()
    
    # Zbierz pełną odpowiedź (nie streaming)
    full_response = ""
    for chunk in service.stream_chat(user_message, history, hd_data, user_id):
        full_response += chunk
    
    return full_response

# 🔹 Streaming version (refactored - używa HDChatService)
def stream_chat_with_hd_ai(user_message: str, history: list[dict] = None, hd_data: dict = None, user_id: str = None):
    """
    Streaming version of HD chat.
    Używa HDChatService do zachowania kompatybilności wstecznej.
    """
    if history is None:
        history = []
    if hd_data is None:
        hd_data = {}

    # Użyj HDChatService do streaming
    service = HDChatService()
    yield from service.stream_chat(user_message, history, hd_data, user_id)

# 🔹 Helper function to save chat messages
def save_chat_message(db: Session, session_id: str, role: str, content: str):
    """Save a chat message to the database"""
    message = ChatMessage(
        id=f"msg-{int(os.urandom(4).hex(), 16)}",
        session_id=session_id,
        role=role,
        content=content
    )
    db.add(message)
    db.commit()

# 🔹 Get chat history from database
def get_hd_chat_history_from_db(db: Session, session_id: str) -> list[dict]:
    """Pobiera historię czatu HD z bazy danych"""
    from app.modules.hd.models import HDChatMessage
    
    messages = db.query(HDChatMessage).filter(
        HDChatMessage.session_id == session_id
    ).order_by(HDChatMessage.message_order, HDChatMessage.created_at).all()
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]