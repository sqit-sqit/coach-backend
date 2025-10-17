from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from pathlib import Path
from pydantic import BaseModel
from typing import Optional
import os
import json
import subprocess
import sys

from app.core.database import get_db
from app.modules.values.models import ValuesSession, ValuesChatMessage, ValuesSummary
from app.core.models import User, AppSession
from app.config.ai_models import AI_MODELS, AVAILABLE_MODELS, get_model_config

router = APIRouter(tags=["admin"], prefix="/admin")

# 🔐 Simple admin authentication
def verify_admin_key(admin_key: str = Query(..., description="Admin access key")):
    """
    Weryfikuje klucz admina.
    W produkcji użyj mocnego klucza i przechowuj w .env
    """
    correct_key = os.getenv("ADMIN_SECRET_KEY", "dev-admin-key-123")
    
    if admin_key != correct_key:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    
    return True


@router.get("/conversations")
def get_all_conversations(
    admin_key: str = Query(...),
    limit: int = Query(50, description="Number of sessions to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Pobiera wszystkie konwersacje użytkowników z pełną historią.
    
    Wymaga admin_key w query params:
    /admin/conversations?admin_key=your-secret-key
    """
    # Verify admin key
    verify_admin_key(admin_key)
    
    db = next(get_db())
    
    try:
        # Pobierz sesje wartości
        sessions = db.query(ValuesSession).order_by(
            desc(ValuesSession.started_at)
        ).limit(limit).offset(offset).all()
        
        result = []
        
        for session in sessions:
            # Pobierz user info z app_sessions
            user_info = db.query(AppSession).filter(
                AppSession.user_id == session.user_id,
                AppSession.app_name == "values",
                AppSession.status == "active"
            ).first()
            
            user_name = "Unknown"
            user_age = None
            user_interests = []
            
            if user_info and user_info.session_data:
                init_data = user_info.session_data.get("init", {}).get("data", {})
                user_name = init_data.get("name", "Guest")
                user_age = init_data.get("age_range")
                user_interests = init_data.get("interests", [])
            
            # Pobierz wiadomości
            messages = db.query(ValuesChatMessage).filter(
                ValuesChatMessage.session_id == session.session_id
            ).order_by(ValuesChatMessage.message_order).all()
            
            # Pobierz podsumowanie
            summary = db.query(ValuesSummary).filter(
                ValuesSummary.session_id == session.session_id
            ).first()
            
            result.append({
                "session_id": session.session_id,
                "user_id": session.user_id,
                "user_name": user_name,
                "user_age": user_age,
                "user_interests": user_interests,
                "chosen_value": session.chosen_value,
                "started_at": session.started_at.isoformat() if session.started_at else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "status": session.status,
                "chat_mode": session.chat_mode,
                "message_count": len(messages),
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat() if msg.created_at else None,
                        "is_summary": msg.is_summary
                    }
                    for msg in messages
                ],
                "summary": summary.summary_content if summary else None
            })
    
        total_count = db.query(ValuesSession).count()
        
        return {
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "conversations": result
        }
    except Exception as e:
        print(f"Admin conversations error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")
    finally:
        db.close()


@router.get("/stats")
def get_admin_stats(
    admin_key: str = Query(...)
):
    """
    Zwraca statystyki użytkowania aplikacji.
    """
    # Verify admin key
    verify_admin_key(admin_key)
    
    db = next(get_db())
    
    try:
        total_users = db.query(User).count()
        total_sessions = db.query(ValuesSession).count()
        completed_sessions = db.query(ValuesSession).filter(
            ValuesSession.status == "completed"
        ).count()
        
        # Sesje z ostatnich 7 dni
        week_ago = datetime.now() - timedelta(days=7)
        recent_sessions = db.query(ValuesSession).filter(
            ValuesSession.started_at >= week_ago
        ).count()
        
        # Top values - simplified query
        from sqlalchemy import func
        top_values_query = db.query(
            ValuesSession.chosen_value,
            func.count(ValuesSession.chosen_value).label('value_count')
        ).filter(
            ValuesSession.chosen_value != None
        ).group_by(
            ValuesSession.chosen_value
        ).order_by(
            desc('value_count')
        ).limit(10)
        
        top_values = top_values_query.all()
        
        return {
            "total_users": total_users,
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "recent_sessions_7d": recent_sessions,
            "completion_rate": f"{(completed_sessions / total_sessions * 100):.1f}%" if total_sessions > 0 else "0%",
            "top_values": [
                {"value": v[0], "count": v[1]} 
                for v in top_values
            ]
        }
    except Exception as e:
        print(f"Admin stats error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
    finally:
        db.close()


@router.get("/users")
def get_all_users(
    admin_key: str = Query(...),
    limit: int = Query(100, description="Number of users to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """
    Pobiera listę wszystkich zarejestrowanych użytkowników z informacjami o aktywności.
    
    Wymaga admin_key w query params:
    /admin/users?admin_key=your-secret-key
    """
    # Verify admin key
    verify_admin_key(admin_key)
    
    db = next(get_db())
    
    try:
        # Pobierz użytkowników z informacjami o aktywności
        users = db.query(User).order_by(desc(User.created_at)).limit(limit).offset(offset).all()
        
        result = []
        
        for user in users:
            # Znajdź ostatnią aktywność (ostatnia sesja)
            last_activity = db.query(AppSession).filter(
                AppSession.user_id == user.user_id
            ).order_by(desc(AppSession.started_at)).first()
            
            # Policz liczbę sesji
            total_sessions = db.query(AppSession).filter(
                AppSession.user_id == user.user_id
            ).count()
            
            # Policz sesje z ostatnich 30 dni
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_sessions = db.query(AppSession).filter(
                AppSession.user_id == user.user_id,
                AppSession.started_at >= thirty_days_ago
            ).count()
            
            result.append({
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "is_active": user.is_active,
                "last_activity": last_activity.started_at.isoformat() if last_activity else None,
                "total_sessions": total_sessions,
                "recent_sessions_30d": recent_sessions
            })
        
        return {
            "users": result,
            "total_count": db.query(User).count()
        }
        
    except Exception as e:
        print(f"Admin users error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
    finally:
        db.close()


@router.post("/migrate")
def run_database_migration(admin_key: str = Query(...)):
    """
    Ręcznie uruchom migracje bazy danych.
    
    Wymaga admin_key w query params:
    /admin/migrate?admin_key=your-secret-key
    """
    # Verify admin key
    verify_admin_key(admin_key)
    
    try:
        print("🔄 Running database migrations manually...")
        
        # Get the project root directory (parent of app directory)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=project_root)
        
        if result.returncode == 0:
            return {
                "success": True,
                "message": "Database migrations completed successfully",
                "output": result.stdout
            }
        else:
            return {
                "success": False,
                "message": "Migration failed",
                "error": result.stderr,
                "output": result.stdout
            }
            
    except Exception as e:
        print(f"Migration error: {e}")
        raise HTTPException(status_code=500, detail=f"Error running migrations: {str(e)}")


# 🤖 AI Model Configuration Endpoints

class ModelConfigUpdate(BaseModel):
    model: str
    temperature: float
    max_tokens: Optional[int] = None


@router.get("/ai-models")
def get_ai_models_config(
    admin_key: str = Query(...)
):
    """
    Pobierz konfigurację modeli AI dla wszystkich apek.
    
    Wymaga admin_key w query params:
    /admin/ai-models?admin_key=your-secret-key
    """
    # Verify admin key
    verify_admin_key(admin_key)
    
    return {
        "configs": AI_MODELS,
        "available_models": AVAILABLE_MODELS
    }


@router.put("/ai-models/{app_name}")
def update_ai_model_config(
    app_name: str,
    config: ModelConfigUpdate,
    admin_key: str = Query(...)
):
    """
    Zaktualizuj konfigurację modelu dla danej apki.
    
    Wymaga admin_key w query params:
    PUT /admin/ai-models/values?admin_key=your-secret-key
    
    Body:
    {
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": null
    }
    """
    # Verify admin key
    verify_admin_key(admin_key)
    
    if config.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid model name. Available models: {AVAILABLE_MODELS}"
        )
    
    if not (0 <= config.temperature <= 1):
        raise HTTPException(
            status_code=400,
            detail="Temperature must be between 0 and 1"
        )
    
    # Aktualizuj w pamięci
    if app_name not in AI_MODELS:
        AI_MODELS[app_name] = {
            "description": f"{app_name.capitalize()} app"
        }
    
    AI_MODELS[app_name]["model"] = config.model
    AI_MODELS[app_name]["temperature"] = config.temperature
    AI_MODELS[app_name]["max_tokens"] = config.max_tokens
    
    # Zapisz do pliku (żeby przetrwało restart)
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "ai_models.py"
        
        # Przygotuj zawartość pliku
        new_content = f'''"""
AI Model Configuration for Mini-Apps
Edit this file to change AI models for each app.
Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
from datetime import datetime

AI_MODELS = {json.dumps(AI_MODELS, indent=4)}

# Fallback jeśli apka nie ma konfiguracji
DEFAULT_CONFIG = {{
    "model": "gpt-4o-mini",
    "temperature": 0.7,
    "max_tokens": None
}}

def get_model_config(app_name: str) -> dict:
    """Pobierz konfigurację modelu dla danej apki"""
    return AI_MODELS.get(app_name, DEFAULT_CONFIG)

# Dostępne modele OpenAI (dla referencji)
AVAILABLE_MODELS = {json.dumps(AVAILABLE_MODELS, indent=4)}
'''
        
        with open(config_path, 'w') as f:
            f.write(new_content)
        
        print(f"✅ AI model config saved to file for {app_name}")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not save to file: {e}")
        # Continue anyway - config is updated in memory
    
    return {
        "status": "success",
        "app_name": app_name,
        "config": AI_MODELS[app_name],
        "message": f"AI model configuration updated for {app_name}"
    }

