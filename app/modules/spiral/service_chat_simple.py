# app/modules/spiral/service_chat_simple.py
import os
import yaml
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.spiral.models import SpiralSession, SpiralChatMessage
from app.config.ai_models import get_model_config

# załaduj zmienne z .env
load_dotenv()

# 🔹 Wczytywanie pliku osobowości
def load_spiral_personality(initial_problem: str = "not specified", current_cycle: int = 1, prompt_template: str = "", user_name: str = "Guest") -> str:
    """
    Ładuje osobowość Spiral z pliku i podstawia zmienne.
    """
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    file_path = base_dir / "spiral_personality_chat.txt"

    if not file_path.exists():
        return "You are a helpful AI assistant for spiral reflection."

    raw = file_path.read_text(encoding="utf-8")
    return (raw
        .replace("{initial_problem}", initial_problem)
        .replace("{current_cycle}", str(current_cycle))
        .replace("{prompt_template}", prompt_template)
        .replace("{name}", user_name)
    )


# 🔹 Wczytywanie pliku z szablonem pytań
def load_prompt_template(file_name: str = "spiral_session_template.yaml") -> str:
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    file_path = base_dir / file_name

    if not file_path.exists():
        return ""
    
    # Obsługa plików YAML
    if file_name.endswith('.yaml') or file_name.endswith('.yml'):
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Konwertuj YAML na tekst formatowany
        result = []
        
        # Sprawdź czy to lista sekcji (wielosekcyjny format) czy jedna sekcja
        if isinstance(data, list):
            # Format wielosekcyjny (jak spiral_session_template.yaml)
            for section in data:
                result.append(f"## {section['section']}")
                result.append(f"### {section['title']}")
                if 'intro' in section:
                    result.append(section['intro'])
                if 'questions' in section:
                    for question in section['questions']:
                        result.append(f"- {question}")
                if 'paraphrase_instruction' in section:
                    result.append(f"\n**Paraphrase Instruction:** {section['paraphrase_instruction']}")
                if 'reflection' in section:
                    result.append(f"\n**Reflection:** {section['reflection']}")
                result.append("")  # Pusta linia między sekcjami
        else:
            # Format jednosekcyjny
            section = data
            result.append(f"## {section['section']}")
            result.append(f"### {section['title']}")
            if 'intro' in section:
                result.append(section['intro'])
            if 'questions' in section:
                for question in section['questions']:
                    result.append(f"- {question}")
            if 'paraphrase_instruction' in section:
                result.append(f"\n**Paraphrase Instruction:** {section['paraphrase_instruction']}")
            if 'reflection' in section:
                result.append(f"\n**Reflection:** {section['reflection']}")
        
        return "\n".join(result)
    
    # Obsługa plików TXT (fallback)
    return file_path.read_text(encoding="utf-8")


def save_chat_message(db: Session, session_id: str, role: str, content: str):
    """Zapisuje wiadomość czatu do bazy danych"""
    # Znajdź ostatni message_order
    last_message = db.query(SpiralChatMessage).filter(
        SpiralChatMessage.session_id == session_id
    ).order_by(SpiralChatMessage.message_order.desc()).first()
    
    next_order = (last_message.message_order + 1) if last_message else 1
    
    message = SpiralChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        message_order=next_order
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_or_create_spiral_session(db: Session, user_id: str, initial_problem: str = None) -> SpiralSession:
    """Pobiera lub tworzy sesję spiral dla użytkownika"""
    session = db.query(SpiralSession).filter(
        SpiralSession.user_id == user_id,
        SpiralSession.status == "active"
    ).first()
    
    if not session:
        # Utwórz nową sesję
        session = SpiralSession(
            user_id=user_id,
            session_id=f"{user_id}-spiral-session",
            initial_problem=initial_problem,
            status="active"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    
    return session


def get_chat_history_from_db(db: Session, session_id: str) -> list[dict]:
    """Pobiera historię czatu z bazy danych"""
    messages = db.query(SpiralChatMessage).filter(
        SpiralChatMessage.session_id == session_id
    ).order_by(SpiralChatMessage.message_order).all()
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


# 🔹 Główna funkcja czatu
def chat_with_spiral_ai(user_message: str, history: list[dict] = None, initial_problem: str = None, current_cycle: int = 1, user_id: str = None) -> str:
    """
    Tworzy odpowiedź AI bazując na historii rozmowy i pliku osobowości.
    """
    if history is None:
        history = []

    # Pobierz imię użytkownika
    user_name = "Guest"  # Można dodać logikę pobierania imienia z bazy
    
    # Wczytaj personality + template
    prompt_template = load_prompt_template("spiral_session_template.yaml")
    system_prompt = load_spiral_personality(initial_problem or "not specified", current_cycle, prompt_template, user_name)

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
        # Rozpoczęcie sesji spiral - AI powinno zacząć od intro z YAML
        messages.append({"role": "user", "content": "Start the spiral reflection session. Begin with the intro from the YAML template."})
    else:
        messages.append({"role": "user", "content": user_message})

    # Pobierz konfigurację modelu
    model_config = get_model_config("spiral_chat")
    
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
            session = get_or_create_spiral_session(db, user_id, initial_problem)
            
            # Zapisz wiadomość użytkownika
            save_chat_message(db, session.session_id, "user", user_message)
            
            # Zapisz odpowiedź AI
            save_chat_message(db, session.session_id, "assistant", response)
            
        finally:
            db.close()

    return response


def stream_chat_with_spiral_ai(user_message: str, history: list[dict] | None = None, initial_problem: str = None, current_cycle: int = 1, user_id: str = None):
    """
    Streamuje odpowiedź AI w kawałkach (chunkach) jako generator.
    """
    if history is None:
        history = []

    # Pobierz imię użytkownika
    user_name = "Guest"  # Można dodać logikę pobierania imienia z bazy
    
    # Wczytaj personality + template
    prompt_template = load_prompt_template("spiral_session_template.yaml")
    system_prompt = load_spiral_personality(initial_problem or "not specified", current_cycle, prompt_template, user_name)

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
        # Rozpoczęcie sesji spiral - AI powinno zacząć od intro z YAML
        messages.append({"role": "user", "content": "Start the spiral reflection session. Begin with the intro from the YAML template."})
    else:
        messages.append({"role": "user", "content": user_message})

    # Pobierz konfigurację modelu
    model_config = get_model_config("spiral_chat")
    
    # Wywołaj OpenAI ze streamingiem i konfiguracją
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
            session = get_or_create_spiral_session(db, user_id, initial_problem)
            save_chat_message(db, session.session_id, "user", user_message)
        finally:
            db.close()

    for chunk in stream:
        if chunk.choices[0].delta.content is not None:
            content = chunk.choices[0].delta.content
            full_response += content
            yield content

    # Zapisz pełną odpowiedź AI do bazy jeśli user_id jest podany
    if user_id and full_response:
        db = next(get_db())
        try:
            session = get_or_create_spiral_session(db, user_id, initial_problem)
            save_chat_message(db, session.session_id, "assistant", full_response)
        finally:
            db.close()

