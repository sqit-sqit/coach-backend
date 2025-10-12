from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from app.core.database import get_db
from app.modules.values.models import ValuesSession, ValuesChatMessage, ValuesSummary
from app.core.models import User, AppSession
import os

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

