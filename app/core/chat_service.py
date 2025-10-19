# app/core/chat_service.py
"""
BaseChatService - wspólny serwis bazowy dla wszystkich aplikacji chat.

Zawiera wspólną logikę streaming, OpenAI client, error handling,
ale pozwala na specjalizację dla każdej aplikacji.
"""
import os
from typing import Generator, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from app.config.ai_models import get_model_config

# załaduj zmienne z .env
load_dotenv()


class BaseChatService:
    """
    Bazowa klasa dla wszystkich chat services.
    Zawiera wspólną logikę streaming, OpenAI client, error handling.
    """
    
    def __init__(self, app_type: str):
        """
        Inicjalizuje serwis dla określonego typu aplikacji.
        
        Args:
            app_type: Typ aplikacji ("values", "hd", etc.)
        """
        self.app_type = app_type
    
    def _get_openai_client(self) -> OpenAI:
        """
        Tworzy i zwraca skonfigurowany klient OpenAI.
        
        Returns:
            OpenAI: Skonfigurowany klient OpenAI
            
        Raises:
            RuntimeError: Jeśli OPENAI_API_KEY nie jest ustawiony
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in .env")
        return OpenAI(api_key=api_key)
    
    def _get_model_config(self) -> Dict[str, Any]:
        """
        Pobiera konfigurację modelu AI dla danej aplikacji.
        
        Returns:
            Dict[str, Any]: Konfiguracja modelu (model, temperature, max_tokens)
        """
        return get_model_config(f"{self.app_type}_chat")
    
    def _prepare_messages(self, system_prompt: str, history: list[dict], user_message: str) -> list[dict]:
        """
        Przygotowuje wiadomości dla OpenAI API.
        
        Args:
            system_prompt: Prompt systemowy
            history: Historia rozmowy
            user_message: Wiadomość użytkownika
            
        Returns:
            list[dict]: Lista wiadomości dla OpenAI
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        
        if not user_message.strip():
            messages.append({"role": "user", "content": self._get_start_message()})
        else:
            messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _get_start_message(self) -> str:
        """
        Zwraca wiadomość startową dla danej aplikacji.
        Każda aplikacja implementuje swoją wiadomość startową.
        
        Returns:
            str: Wiadomość startowa
            
        Raises:
            NotImplementedError: Jeśli nie jest zaimplementowane w klasie potomnej
        """
        raise NotImplementedError("Subclasses must implement _get_start_message")
    
    def stream_chat(self, user_message: str, history: list[dict], context_data: Dict[str, Any], user_id: str = None) -> Generator[str, None, None]:
        """
        Główna metoda streaming chat - wspólna dla wszystkich aplikacji.
        
        Args:
            user_message: Wiadomość użytkownika
            history: Historia rozmowy
            context_data: Dane kontekstowe (specyficzne dla aplikacji)
            user_id: ID użytkownika (opcjonalne)
            
        Yields:
            str: Kolejne fragmenty odpowiedzi AI
        """
        # 1. Pobierz system prompt (implementuje każda aplikacja)
        system_prompt = self._load_personality(context_data)
        
        # 2. Przygotuj wiadomości
        messages = self._prepare_messages(system_prompt, history, user_message)
        
        # 3. Konfiguracja OpenAI
        client = self._get_openai_client()
        model_config = self._get_model_config()
        
        # 4. Streaming
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
            self._save_user_message(user_message, user_id, context_data)
        
        # Streamuj odpowiedź
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                content = chunk.choices[0].delta.content
                full_response += content
                yield content
        
        # Zapisz pełną odpowiedź AI do bazy jeśli user_id jest podany
        if user_id and full_response:
            self._save_ai_message(full_response, user_id, context_data)
    
    def _load_personality(self, context_data: Dict[str, Any]) -> str:
        """
        Ładuje personality dla danej aplikacji.
        Każda aplikacja implementuje swoją logikę ładowania personality.
        
        Args:
            context_data: Dane kontekstowe (specyficzne dla aplikacji)
            
        Returns:
            str: System prompt z personality
            
        Raises:
            NotImplementedError: Jeśli nie jest zaimplementowane w klasie potomnej
        """
        raise NotImplementedError("Subclasses must implement _load_personality")
    
    def _save_user_message(self, user_message: str, user_id: str, context_data: Dict[str, Any]):
        """
        Zapisuje wiadomość użytkownika do bazy danych.
        Każda aplikacja implementuje swoją logikę zapisywania.
        
        Args:
            user_message: Wiadomość użytkownika
            user_id: ID użytkownika
            context_data: Dane kontekstowe (specyficzne dla aplikacji)
            
        Raises:
            NotImplementedError: Jeśli nie jest zaimplementowane w klasie potomnej
        """
        raise NotImplementedError("Subclasses must implement _save_user_message")
    
    def _save_ai_message(self, ai_response: str, user_id: str, context_data: Dict[str, Any]):
        """
        Zapisuje odpowiedź AI do bazy danych.
        Każda aplikacja implementuje swoją logikę zapisywania.
        
        Args:
            ai_response: Odpowiedź AI
            user_id: ID użytkownika
            context_data: Dane kontekstowe (specyficzne dla aplikacji)
            
        Raises:
            NotImplementedError: Jeśli nie jest zaimplementowane w klasie potomnej
        """
        raise NotImplementedError("Subclasses must implement _save_ai_message")
