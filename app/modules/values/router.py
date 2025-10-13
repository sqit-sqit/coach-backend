from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.core.models import User, AppSession
from app.routers.auth import get_current_user_from_token
from app.modules.values.models import ValuesSession, ValuesChatMessage, ValuesSummary
from . import service_init, schemas, service_chat, service_feedback

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
def get_selected(user_id: str):
    # Allow both authenticated users and guests
    # Guest users have IDs starting with "guest-"
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
def chat_endpoint(user_id: str, req: ChatRequest, db: Session = Depends(get_db)):
    """
    Endpoint chatu z AI.
    Allow both authenticated users and guests.
    """
    
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
def chat_stream_endpoint(user_id: str, req: ChatRequest, db: Session = Depends(get_db)):
    """
    Streamingowy endpoint chatu z AI. Zwraca strumień tekstu.
    Allow both authenticated users and guests.
    """
    
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
def generate_summary_endpoint(user_id: str, req: SummaryRequest, db: Session = Depends(get_db)):
    """
    Generuje podsumowanie sesji eksploracji wartości.
    Allow both authenticated users and guests.
    """
    
    # Pobierz wybraną wartość użytkownika
    chosen_value = service_init.get_chosen_value(user_id)
    if not chosen_value:
        return {"error": "No chosen value found for user"}
    
    # Wygeneruj podsumowanie
    summary = service_chat.generate_summary(
        value=chosen_value,
        chat_history=req.chat_history,
        reflection_history=req.reflection_history,
        user_id=user_id
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


# ---------- USER DASHBOARD ----------
@router.get("/user/{user_id}/dashboard")
def get_user_dashboard(user_id: str, db: Session = Depends(get_db)):
    """
    Zwraca dane dla dashboard użytkownika:
    - Historia sesji wartości
    - Statystyki
    - Progress
    """
    # Pobierz wszystkie sesje wartości użytkownika
    sessions = db.query(ValuesSession).filter(
        ValuesSession.user_id == user_id
    ).order_by(desc(ValuesSession.started_at)).all()
    
    # Pobierz app session dla user info
    app_session = db.query(AppSession).filter(
        AppSession.user_id == user_id,
        AppSession.app_name == "values",
        AppSession.status == "active"
    ).first()
    
    result = {
        "user_id": user_id,
        "total_sessions": len(sessions),
        "completed_sessions": len([s for s in sessions if s.status == "completed"]),
        "sessions": []
    }
    
    for session in sessions:
        # Pobierz message count
        message_count = db.query(ValuesChatMessage).filter(
            ValuesChatMessage.session_id == session.session_id
        ).count()
        
        # Pobierz summary
        summary = db.query(ValuesSummary).filter(
            ValuesSummary.session_id == session.session_id
        ).first()
        
        result["sessions"].append({
            "session_id": session.session_id,
            "chosen_value": session.chosen_value,
            "started_at": session.started_at.isoformat() if session.started_at else None,
            "ended_at": session.ended_at.isoformat() if session.ended_at else None,
            "status": session.status,
            "message_count": message_count,
            "has_summary": summary is not None
        })
    
    # Dodaj progress info z app_session
    if app_session and app_session.session_data:
        result["current_progress"] = app_session.session_data
    
    return result


# ---------- FEEDBACK ----------
@router.post("/feedback")
def submit_feedback(feedback: schemas.FeedbackSubmit):
    """
    Zapisuje feedback od użytkownika.
    Automatycznie pobiera dane użytkownika z init phase jeśli nie podano.
    """
    print(f">>> FEEDBACK ENDPOINT CALLED: user_id={feedback.user_id}, rating={feedback.rating}")
    try:
        result = service_feedback.save_feedback(
            user_id=feedback.user_id,
            session_id=feedback.session_id,
            name=feedback.name,
            age_range=feedback.age_range,
            interests=feedback.interests,
            rating=feedback.rating,
            liked_text=feedback.liked_text,
            liked_chips=feedback.liked_chips,
            disliked_text=feedback.disliked_text,
            disliked_chips=feedback.disliked_chips,
            additional_feedback=feedback.additional_feedback
        )
        print(f">>> FEEDBACK SAVED SUCCESSFULLY: {result}")
        return result
    except Exception as e:
        print(f">>> FEEDBACK ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")

@router.get("/feedback/{user_id}")
def get_user_feedback(user_id: str):
    """
    Pobiera feedback dla danego użytkownika.
    """
    feedback = service_feedback.get_feedback(user_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return feedback

@router.get("/feedback")
def get_all_feedback_data(limit: int = 100, offset: int = 0):
    """
    Pobiera wszystkie feedbacki (dla admina).
    """
    return service_feedback.get_all_feedback(limit=limit, offset=offset)