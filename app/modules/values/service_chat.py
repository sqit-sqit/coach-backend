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
def load_prompt_template(file_name: str = "deeper_questions.txt") -> str:
    base_dir = Path(__file__).resolve().parents[2] / "personality"
    file_path = base_dir / file_name

    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


# 🔹 Główna funkcja czatu
def chat_with_ai(user_message: str, history: list[dict] = None, value: str = "your value") -> str:
    """
    Tworzy odpowiedź AI bazując na historii rozmowy i pliku osobowości.
    """
    if history is None:
        history = []

    # Wczytaj personality + template
    prompt_template = load_prompt_template()
    system_prompt = load_personality("value_chat.txt", value, prompt_template)

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


def stream_chat_with_ai(user_message: str, history: list[dict] | None = None, value: str = "your value"):
    """
    Streamuje odpowiedź AI w kawałkach (chunkach) jako generator.

    Zwraca generator, który yielduje kolejne fragmenty pola `content`.
    Użyj bezpośrednio lub opakuj w StreamingResponse po stronie FastAPI, np.:

        from fastapi import StreamingResponse
        return StreamingResponse(stream_chat_with_ai(msg, history), media_type="text/plain")
    """
    if history is None:
        history = []

    prompt_template = load_prompt_template()
    system_prompt = load_personality("value_chat.txt", value, prompt_template)

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