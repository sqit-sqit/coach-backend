from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.hd.models import HDSession
from app.modules.hd.service_chat import chat_with_hd_ai, stream_chat_with_hd_ai
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

class StartChatRequest(BaseModel):
    session_id: str

@router.post("/chat")
async def start_hd_chat(
    request: StartChatRequest,
    db: Session = Depends(get_db)
):
    """
    Rozpoczyna nową rozmowę HD chat dla danej sesji
    """
    try:
        # Pobierz dane sesji HD
        hd_session = db.query(HDSession).filter(HDSession.session_id == request.session_id).first()
        if not hd_session:
            raise HTTPException(status_code=404, detail="HD session not found")
        
        # Przygotuj dane HD
        hd_data = {
            "type": hd_session.type,
            "strategy": hd_session.strategy,
            "authority": hd_session.authority,
            "profile": hd_session.profile,
            "defined_centers": hd_session.defined_centers,
            "undefined_centers": hd_session.undefined_centers,
            "defined_channels": hd_session.defined_channels,
            "active_gates": hd_session.active_gates,
            "activations": hd_session.activations,
            "name": hd_session.name,
            "birth_date": hd_session.birth_date.isoformat() if hd_session.birth_date else None,
            "birth_time": hd_session.birth_time,
            "birth_place": hd_session.birth_place
        }
        
        # Wygeneruj pierwszą wiadomość AI
        first_message = chat_with_hd_ai("", [], hd_data, hd_session.user_id)
        
        return {
            "chat_session_id": f"hd-chat-{hd_session.user_id}-{request.session_id}",
            "message": first_message
        }
        
    except Exception as e:
        print(f"Error starting HD chat: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start HD chat: {str(e)}")

@router.post("/chat/{chat_session_id}")
async def send_hd_message(
    chat_session_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Wysyła wiadomość w HD chat (non-streaming)
    """
    try:
        # Wyciągnij session_id z chat_session_id (format: hd-chat-{user_id}-{session_id})
        parts = chat_session_id.split('-')
        if len(parts) < 4:
            raise HTTPException(status_code=400, detail="Invalid chat session ID format")
        
        session_id = '-'.join(parts[3:])  # Wszystko po trzecim myślniku
        
        # Pobierz dane sesji HD
        hd_session = db.query(HDSession).filter(HDSession.session_id == session_id).first()
        if not hd_session:
            raise HTTPException(status_code=404, detail="HD session not found")
        
        # Przygotuj dane HD
        hd_data = {
            "type": hd_session.type,
            "strategy": hd_session.strategy,
            "authority": hd_session.authority,
            "profile": hd_session.profile,
            "defined_centers": hd_session.defined_centers,
            "undefined_centers": hd_session.undefined_centers,
            "defined_channels": hd_session.defined_channels,
            "active_gates": hd_session.active_gates,
            "activations": hd_session.activations,
            "name": hd_session.name,
            "birth_date": hd_session.birth_date.isoformat() if hd_session.birth_date else None,
            "birth_time": hd_session.birth_time,
            "birth_place": hd_session.birth_place
        }
        
        # Wygeneruj odpowiedź AI
        response = chat_with_hd_ai(request.message, request.history, hd_data, hd_session.user_id)
        
        return {
            "response": response,
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
    except Exception as e:
        print(f"Error processing HD message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.post("/chat/{chat_session_id}/stream")
async def send_hd_message_stream(
    chat_session_id: str,
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Wysyła wiadomość w HD chat (streaming)
    """
    try:
        # Wyciągnij session_id z chat_session_id (format: hd-chat-{user_id}-{session_id})
        parts = chat_session_id.split('-')
        if len(parts) < 4:
            raise HTTPException(status_code=400, detail="Invalid chat session ID format")
        
        session_id = '-'.join(parts[3:])  # Wszystko po trzecim myślniku
        
        # Pobierz dane sesji HD
        hd_session = db.query(HDSession).filter(HDSession.session_id == session_id).first()
        if not hd_session:
            raise HTTPException(status_code=404, detail="HD session not found")
        
        # Przygotuj dane HD
        hd_data = {
            "type": hd_session.type,
            "strategy": hd_session.strategy,
            "authority": hd_session.authority,
            "profile": hd_session.profile,
            "defined_centers": hd_session.defined_centers,
            "undefined_centers": hd_session.undefined_centers,
            "defined_channels": hd_session.defined_channels,
            "active_gates": hd_session.active_gates,
            "activations": hd_session.activations,
            "name": hd_session.name,
            "birth_date": hd_session.birth_date.isoformat() if hd_session.birth_date else None,
            "birth_time": hd_session.birth_time,
            "birth_place": hd_session.birth_place
        }
        
        # Wygeneruj streaming odpowiedź AI
        generator = stream_chat_with_hd_ai(request.message, request.history, hd_data, hd_session.user_id)
        
        return StreamingResponse(generator, media_type="text/plain; charset=utf-8")
        
    except Exception as e:
        print(f"Error processing HD message stream: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.get("/chat/{chat_session_id}/history")
async def get_hd_chat_history(
    chat_session_id: str,
    db: Session = Depends(get_db)
):
    """
    Pobiera historię rozmowy HD chat
    """
    try:
        # Wyciągnij session_id z chat_session_id (format: hd-chat-{user_id}-{session_id})
        parts = chat_session_id.split('-')
        if len(parts) < 4:
            raise HTTPException(status_code=400, detail="Invalid chat session ID format")
        
        session_id = '-'.join(parts[3:])  # Wszystko po trzecim myślniku
        
        # Pobierz historię z bazy danych
        from app.modules.hd.service_chat import get_hd_chat_history_from_db
        history = get_hd_chat_history_from_db(db, session_id)
        
        return {"messages": history}
        
    except Exception as e:
        print(f"Error getting HD chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get chat history")
