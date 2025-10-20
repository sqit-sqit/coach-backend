"""
AI Model Configuration for Mini-Apps
Edit this file to change AI models for each app.
Last updated: 2025-10-19 17:29:14
"""
from datetime import datetime

AI_MODELS = {
    "values": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": None,
        "description": "Values Workshop - empathetic coaching"
    },
    "hd_chat": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": None,
        "description": "Human Design Chat - specialized HD guidance"
    },
    "grow": {
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "max_tokens": None,
        "description": "Growth Path - future planning"
    },
    "spiral_chat": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": None,
        "description": "Spiral Method - deep reflection guidance"
    }
}

# Fallback jeśli apka nie ma konfiguracji
DEFAULT_CONFIG = {
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": None
}

def get_model_config(app_name: str) -> dict:
    """Pobierz konfigurację modelu dla danej apki"""
    return AI_MODELS.get(app_name, DEFAULT_CONFIG)

# Dostępne modele OpenAI (dla referencji)
AVAILABLE_MODELS = [
    "auto",
    "gpt-5",
    "gpt-5-chat",
    "gpt-5-mini",
    "gpt-5-pro",
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4-turbo"
]
