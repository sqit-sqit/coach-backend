# app/modules/values/service_chat.py
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from . import service_init

# załaduj zmienne z .env
load_dotenv()

# 🔹 Wczytywanie pliku osobowości
def load_personality(file_name: str, value: str, prompt_template: str) -> str:
    """
    Ładuje osobowość z pliku i podstawia zmienne {value} oraz {prompt_template}.
    """
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    file_path = base_dir / file_name

    if not file_path.exists():
        return "You are a helpful assistant."

    raw = file_path.read_text(encoding="utf-8")
    return raw.replace("{value}", value).replace("{prompt_template}", prompt_template)


# 🔹 Wczytywanie pliku z szablonem pytań
def load_prompt_template(file_name: str = "value_deeper_questions.txt") -> str:
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    file_path = base_dir / file_name

    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


# 🔹 Główna funkcja czatu
def chat_with_ai(user_message: str, history: list[dict] = None, value: str = "your value", mode: str = "chat") -> str:
    """
    Tworzy odpowiedź AI bazując na historii rozmowy i pliku osobowości.
    """
    if history is None:
        history = []

    # Wybierz odpowiednie pliki w zależności od trybu
    if mode == "reflect":
        personality_file = "value_personality_session_reflect.txt"
        prompt_file = "value_session_reflect_questions.txt"
    else:  # default "chat"
        personality_file = "value_personality_chat.txt"
        prompt_file = "value_deeper_questions.txt"

    # Wczytaj personality + template
    prompt_template = load_prompt_template(prompt_file)
    system_prompt = load_personality(personality_file, value, prompt_template)

    # Pobierz klucz API
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in .env")

    client = OpenAI(api_key=api_key)

    # Zbuduj wiadomości dla modelu
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)   # historia już ma role: user/assistant
    messages.append({"role": "user", "content": user_message})

    # Wywołaj OpenAI
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )

    return completion.choices[0].message.content


def stream_chat_with_ai(user_message: str, history: list[dict] | None = None, value: str = "your value", mode: str = "chat"):
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
        prompt_file = "value_session_reflect_questions.txt"
    else:  # default "chat"
        personality_file = "value_personality_chat.txt"
        prompt_file = "value_deeper_questions.txt"

    prompt_template = load_prompt_template(prompt_file)
    system_prompt = load_personality(personality_file, value, prompt_template)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in .env")

    client = OpenAI(api_key=api_key)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        stream=True,
    )

    for chunk in stream:
        try:
            choice = chunk.choices[0]
        except Exception:
            continue

        # `delta` moze zawierac tylko czesc contentu
        delta = getattr(choice, "delta", None)
        if not delta:
            continue

        content_piece = None
        # SDK potrafi zwrócić obiekt z atrybutem `content` lub dict
        if hasattr(delta, "content"):
            content_piece = delta.content
        elif isinstance(delta, dict):
            content_piece = delta.get("content")

        if content_piece:
            yield content_piece


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