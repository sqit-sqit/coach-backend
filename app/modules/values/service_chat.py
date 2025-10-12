# app/modules/values/service_chat.py
import os
import yaml
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.values.models import ValuesSession, ValuesChatMessage
from . import service_init

# załaduj zmienne z .env
load_dotenv()

# 🔹 Wczytywanie pliku osobowości
def load_personality(file_name: str, value: str, prompt_template: str, user_name: str = "Guest") -> str:
    """
    Ładuje osobowość z pliku i podstawia zmienne {value}, {prompt_template}, i {name}.
    """
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    file_path = base_dir / file_name

    if not file_path.exists():
        return "You are a helpful assistant."

    raw = file_path.read_text(encoding="utf-8")
    return (raw
        .replace("{value}", value)
        .replace("{prompt_template}", prompt_template)
        .replace("{name}", user_name)
        .replace("{wartosc}", value)  # dla polskich pytań w YAML
    )


# 🔹 Wczytywanie pliku z szablonem pytań
def load_prompt_template(file_name: str = "value_deeper_questions.yaml") -> str:
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
            # Format wielosekcyjny (jak value_deeper_questions.yaml)
            for section in data:
                result.append(f"## {section['section']}")
                result.append(f"### {section['title']}")
                if 'intro' in section:
                    result.append(section['intro'])
                if 'questions' in section:
                    for question in section['questions']:
                        result.append(f"- {question}")
                if 'reflection' in section:
                    result.append(f"\n**Reflection:** {section['reflection']}")
                result.append("")  # Pusta linia między sekcjami
        else:
            # Format jednosekcyjny (jak value_session_reflect_questions.yaml)
            section = data
            result.append(f"## {section['section']}")
            result.append(f"### {section['title']}")
            if 'intro' in section:
                result.append(section['intro'])
            if 'questions' in section:
                for question in section['questions']:
                    result.append(f"- {question}")
            if 'reflection' in section:
                result.append(f"\n**Reflection:** {section['reflection']}")
        
        return "\n".join(result)
    
    # Obsługa plików TXT (fallback)
    return file_path.read_text(encoding="utf-8")


def save_chat_message(db: Session, user_id: str, session_id: str, role: str, content: str):
    """Zapisuje wiadomość czatu do bazy danych"""
    # Użyj prostego podejścia - nie licz wiadomości, użyj timestamp
    message = ValuesChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        message_order=0  # Tymczasowo 0, można później dodać logikę
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_or_create_values_session(db: Session, user_id: str) -> ValuesSession:
    """Pobiera lub tworzy sesję values dla użytkownika"""
    session = db.query(ValuesSession).filter(
        ValuesSession.user_id == user_id,
        ValuesSession.status == "in_progress"
    ).first()
    
    if not session:
        # Sprawdź czy istnieje sesja z tym samym session_id
        existing_session = db.query(ValuesSession).filter(
            ValuesSession.session_id == f"{user_id}-values-session"
        ).first()
        
        if existing_session:
            # Użyj istniejącej sesji i zaktualizuj status
            existing_session.status = "in_progress"
            session = existing_session
        else:
            # Utwórz nową sesję
            session = ValuesSession(
                user_id=user_id,
                session_id=f"{user_id}-values-session",
                status="in_progress"
            )
            db.add(session)
        
        db.commit()
        db.refresh(session)
    
    return session


def get_user_name(user_id: str) -> str:
    """
    Pobiera imię użytkownika z init data.
    Zwraca "Guest" jeśli nie znaleziono.
    """
    try:
        init_data = service_init.get_progress(user_id, "init")
        name = init_data.get("data", {}).get("name", "Guest")
        return name if name else "Guest"
    except:
        return "Guest"


def get_chat_history_from_db(db: Session, user_id: str, session_id: str) -> list[dict]:
    """Pobiera historię czatu z bazy danych"""
    messages = db.query(ValuesChatMessage).filter(
        ValuesChatMessage.user_id == user_id,
        ValuesChatMessage.session_id == session_id
    ).order_by(ValuesChatMessage.timestamp).all()
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


# 🔹 Główna funkcja czatu
def chat_with_ai(user_message: str, history: list[dict] = None, value: str = "your value", mode: str = "chat", user_id: str = None) -> str:
    """
    Tworzy odpowiedź AI bazując na historii rozmowy i pliku osobowości.
    """
    if history is None:
        history = []

    # Wybierz odpowiednie pliki w zależności od trybu
    if mode == "reflect":
        personality_file = "value_personality_session_reflect.txt"
        prompt_file = "value_session_reflect_questions.yaml"
    else:  # default "chat"
        personality_file = "value_personality_chat.txt"
        prompt_file = "value_deeper_questions.yaml"

    # Pobierz imię użytkownika z init data
    user_name = get_user_name(user_id) if user_id else "Guest"
    
    # Wczytaj personality + template
    prompt_template = load_prompt_template(prompt_file)
    system_prompt = load_personality(personality_file, value, prompt_template, user_name)

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
        if mode == "reflect":
            # Rozpoczęcie sesji refleksji - AI powinno zacząć od intro z YAML
            messages.append({"role": "user", "content": f"Start the reflection session for the value '{value}'. Begin with the intro from the YAML template."})
        else:
            # Rozpoczęcie sesji chat - AI powinno zacząć od intro z YAML
            messages.append({"role": "user", "content": f"Start the values workshop for the value '{value}'. Begin with the first question from the YAML template."})
    else:
        messages.append({"role": "user", "content": user_message})

    # Wywołaj OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    response = completion.choices[0].message.content

    # Zapisz wiadomości do bazy jeśli user_id jest podany
    if user_id:
        db = next(get_db())
        try:
            session = get_or_create_values_session(db, user_id)
            
            # Zapisz wiadomość użytkownika
            save_chat_message(db, user_id, session.session_id, "user", user_message)
            
            # Zapisz odpowiedź AI
            save_chat_message(db, user_id, session.session_id, "assistant", response)
            
        finally:
            db.close()

    return response


def stream_chat_with_ai(user_message: str, history: list[dict] | None = None, value: str = "your value", mode: str = "chat", user_id: str = None):
    """
    Streamuje odpowiedź AI w kawałkach (chunkach) jako generator.

    Zwraca generator, który yielduje kolejne fragmenty pola `content`.
    Użyj bezpośrednio lub opakuj w StreamingResponse po stronie FastAPI, np.:

        from fastapi import StreamingResponse
        return StreamingResponse(stream_chat_with_ai(msg, history), media_type="text/plain")
    """
    if history is None:
        history = []

    # Wybierz odpowiednie pliki w zależności od trybu
    if mode == "reflect":
        personality_file = "value_personality_session_reflect.txt"
        prompt_file = "value_session_reflect_questions.yaml"
    else:  # default "chat"
        personality_file = "value_personality_chat.txt"
        prompt_file = "value_deeper_questions.yaml"

    # Pobierz imię użytkownika z init data
    user_name = get_user_name(user_id) if user_id else "Guest"
    
    prompt_template = load_prompt_template(prompt_file)
    system_prompt = load_personality(personality_file, value, prompt_template, user_name)

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
        if mode == "reflect":
            # Rozpoczęcie sesji refleksji - AI powinno zacząć od intro z YAML
            messages.append({"role": "user", "content": f"Start the reflection session for the value '{value}'. Begin with the intro from the YAML template."})
        else:
            # Rozpoczęcie sesji chat - AI powinno zacząć od intro z YAML
            messages.append({"role": "user", "content": f"Start the values workshop for the value '{value}'. Begin with the first question from the YAML template."})
    else:
        messages.append({"role": "user", "content": user_message})

    # Wywołaj OpenAI ze streamingiem
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True
    )

    # Zbierz pełną odpowiedź dla zapisania do bazy
    full_response = ""
    
    # Zapisz wiadomość użytkownika do bazy jeśli user_id jest podany
    if user_id:
        db = next(get_db())
        try:
            session = get_or_create_values_session(db, user_id)
            save_chat_message(db, user_id, session.session_id, "user", user_message)
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
            session = get_or_create_values_session(db, user_id)
            save_chat_message(db, user_id, session.session_id, "assistant", full_response)
        finally:
            db.close()


def generate_summary(value: str, chat_history: list[dict], reflection_history: list[dict] = None) -> str:
    """
    Generuje podsumowanie sesji eksploracji wartości.
    
    Args:
        value: Wybrana wartość użytkownika
        chat_history: Historia czatu z fazy eksploracji wartości
        reflection_history: Historia z fazy refleksji (opcjonalna)
    
    Returns:
        Wygenerowane podsumowanie jako string
    """
    # Wczytaj prompt do podsumowania
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    summary_prompt_file = base_dir / "values_summary_prompt.txt"
    
    if not summary_prompt_file.exists():
        return "Summary generation prompt not found."
    
    summary_prompt = summary_prompt_file.read_text(encoding="utf-8")
    
    # Przygotuj historię czatu jako tekst
    chat_text = ""
    for msg in chat_history:
        role = msg.get("role", "")
        content = msg.get("content", "")
        if role == "user":
            chat_text += f"User: {content}\n"
        elif role == "assistant":
            chat_text += f"Assistant: {content}\n"
    
    # Przygotuj historię refleksji jako tekst
    reflection_text = ""
    if reflection_history:
        for msg in reflection_history:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "user":
                reflection_text += f"User: {content}\n"
            elif role == "assistant":
                reflection_text += f"Assistant: {content}\n"
    
    # Zastąp zmienne w prompcie
    final_prompt = summary_prompt.replace("{wartosc}", value)
    final_prompt = final_prompt.replace("{chat_history}", chat_text)
    final_prompt = final_prompt.replace("{reflection_history}", reflection_text)
    
    # Pobierz klucz API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in .env")
    
    client = OpenAI(api_key=api_key)
    
    # Wywołaj OpenAI z promptem do podsumowania
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a skilled coach creating personalized session summaries."},
            {"role": "user", "content": final_prompt}
        ],
    )
    
    return completion.choices[0].message.content


def save_summary_to_db(user_id: str, session_id: str, summary_text: str):
    """Zapisuje podsumowanie do bazy danych i oznacza sesję jako completed"""
    from datetime import datetime
    db = next(get_db())
    try:
        from app.modules.values.models import ValuesSummary, ValuesSession
        
        # Sprawdź czy podsumowanie już istnieje
        existing_summary = db.query(ValuesSummary).filter(
            ValuesSummary.session_id == session_id
        ).first()
        
        if existing_summary:
            # Aktualizuj istniejące podsumowanie
            existing_summary.summary_content = summary_text
        else:
            # Utwórz nowe podsumowanie
            summary = ValuesSummary(
                session_id=session_id,
                summary_content=summary_text
            )
            db.add(summary)
        
        # WAŻNE: Oznacz sesję jako completed i ustaw ended_at
        session = db.query(ValuesSession).filter(
            ValuesSession.session_id == session_id
        ).first()
        
        if session:
            session.status = "completed"
            session.ended_at = datetime.now()
        
        db.commit()
        
        if existing_summary:
            db.refresh(existing_summary)
            return existing_summary
        else:
            db.refresh(summary)
            return summary
    finally:
        db.close()