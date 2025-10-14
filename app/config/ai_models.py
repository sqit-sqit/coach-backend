"""
AI Model Configuration for Mini-Apps
Edit this file to change AI models for each app.
"""
from datetime import datetime

AI_MODELS = {
    "values": {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": None,
        "description": "Values Workshop - empathetic coaching"
    },
    "grow": {
        "model": "gpt-4o-mini",
        "temperature": 0.8,
        "max_tokens": None,
        "description": "Growth Path - future planning"
    },
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
    # Auto Selection
    "auto",             # Automatyczny wybór najlepszego modelu
    
    # GPT-5 Series (Najnowsze)
    "gpt-5",            # Główna wersja GPT-5 - mocny model ogólnego zastosowania
    "gpt-5-chat",       # Zoptymalizowana pod interakcje konwersacyjne / chat
    "gpt-5-mini",       # Lżejsza, ekonomiczna wersja GPT-5
    "gpt-5-pro",        # Zaawansowany wariant do głębokiego rozumowania
    
    # GPT-4o Series
    "gpt-4o-mini",      # Rekomendowany - najlepszy stosunek jakości do ceny
    "gpt-4o",           # Premium - najwyższa jakość
    "gpt-4-turbo",      # Poprzednia generacja turbo
]

