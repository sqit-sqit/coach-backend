from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import User
from app.routers.auth import get_current_user_from_token
from app.modules.values.models import ValuesSession
from . import service_init, schemas, service_chat

router = APIRouter(tags=["values"])

# ---------- INIT ----------
@router.post("/init/progress")
def update_progress(progress: schemas.InitProgress):
    return service_init.save_progress(
        user_id=progress.user_id,
        phase=progress.phase,
        step=progress.step,
        data=progress.data.dict() if progress.data else None
    )

@router.get("/init/progress/{user_id}")
def read_progress(user_id: str):
    return service_init.get_progress(user_id)

# ---------- SELECT ----------
@router.post("/select")
def save_selected(progress: schemas.ValuesSelect):
    return service_init.save_selected_values(progress.user_id, progress.selected_values)

@router.get("/select/{user_id}")
def get_selected(user_id: str, current_user: User = Depends(get_current_user_from_token)):
    # Sprawdź czy user_id w URL odpowiada zalogowanemu użytkownikowi
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return {"selected_values": service_init.get_selected_values(user_id)}

# ---------- REDUCE ----------
@router.post("/reduce")
def save_reduced(progress: schemas.ValuesReduce):
    return service_init.save_reduced_values(progress.user_id, progress.reduced_values)

@router.get("/reduce/{user_id}")
def get_reduced(user_id: str):
    return {"reduced_values": service_init.get_reduced_values(user_id)}

# ---------- CHOOSE ----------
@router.post("/choose")
def save_chosen(progress: schemas.ValuesChoose):
    return service_init.save_chosen_value(progress.user_id, progress.chosen_value)

@router.get("/choose/{user_id}")
def get_chosen(user_id: str):
    return {"chosen_value": service_init.get_chosen_value(user_id)}

# ---------- VALUES LIST ----------
@router.get("/list")
def get_values():
    """
    Zwraca listę wartości z pliku data/value_list.txt
    """
    base_dir = Path(__file__).resolve().parents[3]
    file_path = base_dir / "data" / "value_list.txt"

    print(">>> [values/list] Looking for file:", file_path)

    if not file_path.exists():
        msg = f"File not found: {file_path}"
        print(">>> [values/list] ERROR:", msg)
        return JSONResponse({"error": msg}, status_code=404)

    try:
        with file_path.open("r", encoding="utf-8") as f:
            values = [line.strip() for line in f if line.strip()]
        print(f">>> [values/list] Loaded {len(values)} values from file.")
        return JSONResponse(values)
    except Exception as e:
        msg = f"Error reading file {file_path}: {e}"
        print(">>> [values/list] ERROR:", msg)
        return JSONResponse({"error": msg}, status_code=500)

# ---------- GAME ----------
@router.post("/game/{user_id}")
def save_game_value(user_id: str, value: dict):
    return service_init.save_top_value(user_id, value["top_value"])

# ---------- CHAT ----------
class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    mode: str = "chat"  # "chat" or "reflect"

class SwitchModeRequest(BaseModel):
    mode: str  # "chat" or "reflect"

class SummaryRequest(BaseModel):
    chat_history: list[dict] = []
    reflection_history: list[dict] = []

@router.post("/chat/{user_id}")
def chat_endpoint(user_id: str, req: ChatRequest, current_user: User = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    """
    Endpoint chatu z AI.
    """
    # Sprawdź czy user_id w URL odpowiada zalogowanemu użytkownikowi
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Pobierz wybraną wartość
    chosen_value = service_init.get_chosen_value(user_id) or "your value"
    
    response = service_chat.chat_with_ai(
        user_message=req.message,
        history=req.history,
        value=chosen_value,
        mode=req.mode,
        user_id=user_id
    )
    return {"reply": response}

@router.post("/chat/{user_id}/stream")
def chat_stream_endpoint(user_id: str, req: ChatRequest, current_user: User = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    """
    Streamingowy endpoint chatu z AI. Zwraca strumień tekstu.
    """
    # Sprawdź czy user_id w URL odpowiada zalogowanemu użytkownikowi
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Pobierz wybraną wartość
    chosen_value = service_init.get_chosen_value(user_id) or "your value"
    
    generator = service_chat.stream_chat_with_ai(
        user_message=req.message,
        history=req.history,
        value=chosen_value,
        mode=req.mode,
        user_id=user_id
    )
    return StreamingResponse(generator, media_type="text/plain; charset=utf-8")

@router.post("/chat/{user_id}/switch-mode")
def switch_mode_endpoint(user_id: str, req: SwitchModeRequest):
    """
    Przełącza tryb personality między 'chat' a 'reflect'.
    """
    # Tutaj można dodać logikę zapisywania trybu dla użytkownika
    # Na razie zwracamy potwierdzenie
    return {
        "status": "success",
        "mode": req.mode,
        "message": f"Switched to {req.mode} mode"
    }

@router.post("/chat/{user_id}/summary")
def generate_summary_endpoint(user_id: str, req: SummaryRequest, current_user: User = Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    """
    Generuje podsumowanie sesji eksploracji wartości.
    """
    # Sprawdź czy user_id w URL odpowiada zalogowanemu użytkownikowi
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Pobierz wybraną wartość użytkownika
    chosen_value = service_init.get_chosen_value(user_id)
    if not chosen_value:
        return {"error": "No chosen value found for user"}
    
    # Wygeneruj podsumowanie
    summary = service_chat.generate_summary(
        value=chosen_value,
        chat_history=req.chat_history,
        reflection_history=req.reflection_history
    )
    
    # Zapisz podsumowanie do bazy
    session = db.query(ValuesSession).filter(
        ValuesSession.user_id == user_id,
        ValuesSession.status == "in_progress"
    ).first()
    
    if session:
        service_chat.save_summary_to_db(user_id, session.session_id, summary)
    
    return {"summary": summary}

@router.get("/chat/{user_id}/history")
def get_chat_history(user_id: str, db: Session = Depends(get_db)):
    """
    Pobiera historię czatu z bazy danych.
    """
    session = db.query(ValuesSession).filter(
        ValuesSession.user_id == user_id,
        ValuesSession.status == "in_progress"
    ).first()
    
    if not session:
        return {"messages": []}
    
    history = service_chat.get_chat_history_from_db(db, user_id, session.session_id)
    return {"messages": history}