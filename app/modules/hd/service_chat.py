# app/modules/hd/service_chat.py
import os
import yaml
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import ChatSession, ChatMessage
from app.config.ai_models import get_model_config

# załaduj zmienne z .env
load_dotenv()

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

# 🔹 Główna funkcja czatu HD
def chat_with_hd_ai(user_message: str, history: list[dict] = None, hd_data: dict = None, user_id: str = None) -> str:
    """
    Tworzy odpowiedź AI bazując na danych HD użytkownika.
    """
    if history is None:
        history = []
    if hd_data is None:
        hd_data = {}

    # Wczytaj personality z danymi HD
    system_prompt = load_hd_personality(hd_data)

    # Pobierz klucz API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in .env")

    client = OpenAI(api_key=api_key)

    # Zbuduj wiadomości dla modelu
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)   # historia już ma role: user/assistant
    
    # Obsługa pierwszej wiadomości (pusta wiadomość = rozpoczęcie sesji)
    if not user_message.strip():
        messages.append({"role": "user", "content": "Start the Human Design conversation. Begin with an introduction about my chart."})
    else:
        messages.append({"role": "user", "content": user_message})

    # Pobierz konfigurację modelu
    model_config = get_model_config("values")  # Używamy tej samej konfiguracji co Values
    
    # Wywołaj OpenAI z konfiguracją
    completion_params = {
        "model": model_config["model"],
        "messages": messages,
        "temperature": model_config["temperature"]
    }
    if model_config["max_tokens"]:
        completion_params["max_tokens"] = model_config["max_tokens"]
    
    completion = client.chat.completions.create(**completion_params)

    response = completion.choices[0].message.content

    # Zapisz wiadomości do bazy jeśli user_id jest podany
    if user_id:
        db = next(get_db())
        try:
            # Znajdź lub stwórz sesję chat
            chat_session = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.session_type == "hd_chat"
            ).first()
            
            if not chat_session:
                chat_session = ChatSession(
                    id=f"hd-chat-{user_id}-{int(os.urandom(4).hex(), 16)}",
                    user_id=user_id,
                    session_type="hd_chat",
                    session_metadata={"hd_data": hd_data}
                )
                db.add(chat_session)
                db.commit()
            
            # Zapisz wiadomość użytkownika
            user_msg = ChatMessage(
                id=f"msg-{int(os.urandom(4).hex(), 16)}",
                session_id=chat_session.id,
                role="user",
                content=user_message
            )
            db.add(user_msg)
            
            # Zapisz odpowiedź AI
            ai_msg = ChatMessage(
                id=f"msg-{int(os.urandom(4).hex(), 16)}",
                session_id=chat_session.id,
                role="assistant",
                content=response
            )
            db.add(ai_msg)
            
            db.commit()
            
        finally:
            db.close()

    return response

# 🔹 Streaming version
def stream_chat_with_hd_ai(user_message: str, history: list[dict] = None, hd_data: dict = None, user_id: str = None):
    """
    Streaming version of HD chat.
    """
    if history is None:
        history = []
    if hd_data is None:
        hd_data = {}

    # Wczytaj personality z danymi HD
    system_prompt = load_hd_personality(hd_data)

    # Pobierz klucz API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in .env")

    client = OpenAI(api_key=api_key)

    # Zbuduj wiadomości dla modelu
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)   # historia już ma role: user/assistant
    
    # Obsługa pierwszej wiadomości (pusta wiadomość = rozpoczęcie sesji)
    if not user_message.strip():
        messages.append({"role": "user", "content": "Start the Human Design conversation. Begin with an introduction about my chart."})
    else:
        messages.append({"role": "user", "content": user_message})

    # Pobierz konfigurację modelu
    model_config = get_model_config("values")  # Używamy tej samej konfiguracji co Values
    
    # Wywołaj OpenAI ze streamingiem
    stream_params = {
        "model": model_config["model"],
        "messages": messages,
        "temperature": model_config["temperature"],
        "stream": True
    }
    if model_config["max_tokens"]:
        stream_params["max_tokens"] = model_config["max_tokens"]
    
    stream = client.chat.completions.create(**stream_params)

    # Zbierz pełną odpowiedź dla zapisania do bazy
    full_response = ""
    
    # Zapisz wiadomość użytkownika do bazy jeśli user_id jest podany
    if user_id:
        db = next(get_db())
        try:
            # Znajdź lub stwórz sesję chat
            chat_session = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.session_type == "hd_chat"
            ).first()
            
            if not chat_session:
                chat_session = ChatSession(
                    id=f"hd-chat-{user_id}-{int(os.urandom(4).hex(), 16)}",
                    user_id=user_id,
                    session_type="hd_chat",
                    session_metadata={"hd_data": hd_data}
                )
                db.add(chat_session)
                db.commit()
            
            save_chat_message(db, chat_session.id, "user", user_message)
        finally:
            db.close()

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            yield content

    # Zapisz pełną odpowiedź AI do bazy jeśli user_id jest podany
    if user_id:
        db = next(get_db())
        try:
            chat_session = db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.session_type == "hd_chat"
            ).first()
            
            if chat_session:
                save_chat_message(db, chat_session.id, "assistant", full_response)
        finally:
            db.close()

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