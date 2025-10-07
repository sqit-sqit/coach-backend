# app/modules/values/service_init.py

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified
from app.core.database import get_db
from app.core.models import User, UserApp, AppSession
from app.modules.values.models import ValuesSession
from typing import Optional


def get_or_create_user(db: Session, user_id: str) -> User:
    """Pobiera lub tworzy użytkownika"""
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(user_id=user_id)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


def get_or_create_user_app(db: Session, user_id: str, app_name: str = "values") -> UserApp:
    """Pobiera lub tworzy rekord UserApp"""
    user_app = db.query(UserApp).filter(
        UserApp.user_id == user_id,
        UserApp.app_name == app_name
    ).first()
    
    if not user_app:
        user_app = UserApp(
            user_id=user_id,
            app_name=app_name,
            usage_count=1
        )
        db.add(user_app)
    else:
        user_app.usage_count += 1
    
    db.commit()
    db.refresh(user_app)
    return user_app


def get_or_create_values_session(db: Session, user_id: str, session_id: str) -> ValuesSession:
    """Pobiera lub tworzy sesję values"""
    session = db.query(ValuesSession).filter(
        ValuesSession.user_id == user_id,
        ValuesSession.session_id == session_id
    ).first()
    
    if not session:
        session = ValuesSession(
            user_id=user_id,
            session_id=session_id,
            status="in_progress"
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def save_progress(user_id: str, phase: str, step: int, data: dict | None = None):
    """
    Zapisuje progres użytkownika dla danej fazy (init, select, reduce, choose...).
    """
    db = next(get_db())
    try:
        # Upewnij się, że użytkownik i app istnieją
        get_or_create_user(db, user_id)
        get_or_create_user_app(db, user_id, "values")
        
        # Znajdź lub stwórz sesję dla tego użytkownika
        session = db.query(AppSession).filter(
            AppSession.user_id == user_id,
            AppSession.app_name == "values",
            AppSession.status == "active"
        ).first()
        
        if not session:
            session = AppSession(
                user_id=user_id,
                app_name="values",
                session_id=f"{user_id}-values-session",
                session_data={}
            )
            db.add(session)
        
        # Zaktualizuj dane sesji - zapisz w formacie {phase: {step, data}}
        current_data = session.session_data or {}
        current_data[phase] = {
            "step": step,
            "data": data or {}
        }
        session.session_data = current_data
        
        # Powiadom SQLAlchemy, że JSON się zmienił
        flag_modified(session, "session_data")
        
        db.commit()
        
        print(">>> SAVE PROGRESS", user_id, phase, step, data)
        
        return {
            "user_id": user_id,
            "phase": phase,
            "step": step,
            "data": data or {}
        }
    finally:
        db.close()


def get_progress(user_id: str, phase: str | None = None):
    """
    Pobiera progres użytkownika:
      - jeśli podasz phase (np. "select"), to zwróci dane tylko z tej fazy
      - jeśli nie podasz, zwróci całość.
    """
    db = next(get_db())
    try:
        session = db.query(AppSession).filter(
            AppSession.user_id == user_id,
            AppSession.app_name == "values",
            AppSession.status == "active"
        ).first()
        
        if not session or not session.session_data:
            return {"step": None, "data": {}} if phase else {}
        
        session_data = session.session_data
        
        if phase:
            phase_data = session_data.get(phase, {"step": None, "data": {}})
            print(">>> GET PROGRESS for", user_id, "phase:", phase, "data:", phase_data)
            return phase_data
        
        print(">>> GET PROGRESS for", user_id, "full data:", session_data)
        return session_data
    finally:
        db.close()


# -----------------------------
#  HELPERY DLA POSZCZEGÓLNYCH FAZ
# -----------------------------

def save_selected_values(user_id: str, values: list[str]):
    """
    Zapisuje wartości z fazy SELECT.
    """
    return save_progress(user_id, "select", 1, {"selected_values": values})


def get_selected_values(user_id: str) -> list[str]:
    """
    Pobiera wartości z fazy SELECT.
    """
    db = next(get_db())
    try:
        session = db.query(AppSession).filter(
            AppSession.user_id == user_id,
            AppSession.app_name == "values",
            AppSession.status == "active"
        ).first()
        
        if not session or not session.session_data:
            return []
        
        select_data = session.session_data.get("select", {})
        result = select_data.get("data", {}).get("selected_values", [])
        return result
    finally:
        db.close()


def save_reduced_values(user_id: str, values: list[str]):
    """
    Zapisuje wartości z fazy REDUCE.
    """
    return save_progress(user_id, "reduce", 1, {"reduced_values": values})


def get_reduced_values(user_id: str) -> list[str]:
    """
    Pobiera wartości z fazy REDUCE.
    """
    db = next(get_db())
    try:
        session = db.query(AppSession).filter(
            AppSession.user_id == user_id,
            AppSession.app_name == "values",
            AppSession.status == "active"
        ).first()
        
        if not session or not session.session_data:
            return []
        
        reduce_data = session.session_data.get("reduce", {})
        return reduce_data.get("data", {}).get("reduced_values", [])
    finally:
        db.close()


def save_chosen_value(user_id: str, value: str):
    """
    Zapisuje pojedynczą wybraną wartość w fazie CHOOSE.
    """
    db = next(get_db())
    try:
        # Zapisz w ValuesSession
        session = get_or_create_values_session(db, user_id, f"{user_id}-values-session")
        session.chosen_value = value
        session.status = "completed"
        db.commit()
        
        # Zapisz też w progress
        return save_progress(user_id, "choose", 1, {"chosen_value": value})
    finally:
        db.close()


def get_chosen_value(user_id: str) -> str | None:
    """
    Pobiera wybraną wartość z fazy CHOOSE.
    """
    db = next(get_db())
    try:
        # Najpierw sprawdź w ValuesSession
        session = db.query(ValuesSession).filter(
            ValuesSession.user_id == user_id
        ).first()
        
        if session and session.chosen_value:
            return session.chosen_value
        
        # Fallback do progress
        return get_progress(user_id, "choose").get("data", {}).get("chosen_value")
    finally:
        db.close()


# Game

def save_top_value(user_id: str, value: str):
    """
    Zapisuje top value z gry.
    """
    return save_progress(user_id, "game", 1, {"top_value": value})


def get_top_value(user_id: str) -> str | None:
    """
    Pobiera top value z gry.
    """
    return get_progress(user_id, "game").get("data", {}).get("top_value")