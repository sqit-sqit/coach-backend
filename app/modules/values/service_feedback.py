# app/modules/values/service_feedback.py

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.models import User
from app.modules.values.models import Feedback
from app.modules.values.service_init import get_progress
from typing import Optional
import json


def save_feedback(
    user_id: str,
    session_id: Optional[str] = None,
    name: Optional[str] = None,
    age_range: Optional[str] = None,
    interests: Optional[list] = None,
    rating: Optional[int] = None,
    liked_text: Optional[str] = None,
    liked_chips: Optional[list] = None,
    disliked_text: Optional[str] = None,
    disliked_chips: Optional[list] = None,
    additional_feedback: Optional[str] = None
):
    """
    Zapisuje feedback od użytkownika.
    Jeśli nie podano danych użytkownika (name, age_range, interests), 
    spróbuje je pobrać z progress data z init phase.
    """
    db = next(get_db())
    try:
        # Jeśli nie podano danych użytkownika, spróbuj pobrać z progress
        if not name or not age_range or not interests:
            progress_data = get_progress(user_id, "init")
            init_data = progress_data.get("data", {})
            
            if not name:
                name = init_data.get("name")
            if not age_range:
                age_range = init_data.get("age_range")
            if not interests:
                interests = init_data.get("interests", [])
        
        # Upewnij się, że użytkownik istnieje
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            user = User(user_id=user_id)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Stwórz feedback record
        feedback = Feedback(
            user_id=user_id,
            session_id=session_id,
            name=name,
            age_range=age_range,
            interests=interests or [],
            rating=rating,
            liked_text=liked_text,
            liked_chips=liked_chips or [],
            disliked_text=disliked_text,
            disliked_chips=disliked_chips or [],
            additional_feedback=additional_feedback
        )
        
        db.add(feedback)
        db.commit()
        db.refresh(feedback)
        
        print(f">>> SAVED FEEDBACK for user {user_id}: rating={rating}, name={name}")
        
        return {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "session_id": feedback.session_id,
            "name": feedback.name,
            "age_range": feedback.age_range,
            "interests": feedback.interests,
            "rating": feedback.rating,
            "liked_text": feedback.liked_text,
            "liked_chips": feedback.liked_chips,
            "disliked_text": feedback.disliked_text,
            "disliked_chips": feedback.disliked_chips,
            "additional_feedback": feedback.additional_feedback,
            "submitted_at": feedback.submitted_at.isoformat()
        }
    finally:
        db.close()


def get_feedback(user_id: str):
    """
    Pobiera feedback dla danego użytkownika.
    """
    db = next(get_db())
    try:
        feedback = db.query(Feedback).filter(
            Feedback.user_id == user_id
        ).order_by(Feedback.submitted_at.desc()).first()
        
        if not feedback:
            return None
            
        return {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "session_id": feedback.session_id,
            "name": feedback.name,
            "age_range": feedback.age_range,
            "interests": feedback.interests,
            "rating": feedback.rating,
            "liked_text": feedback.liked_text,
            "liked_chips": feedback.liked_chips,
            "disliked_text": feedback.disliked_text,
            "disliked_chips": feedback.disliked_chips,
            "additional_feedback": feedback.additional_feedback,
            "submitted_at": feedback.submitted_at.isoformat()
        }
    finally:
        db.close()


def get_all_feedback(limit: int = 100, offset: int = 0):
    """
    Pobiera wszystkie feedbacki (dla admina).
    """
    db = next(get_db())
    try:
        feedbacks = db.query(Feedback).order_by(
            Feedback.submitted_at.desc()
        ).offset(offset).limit(limit).all()
        
        return [
            {
                "id": fb.id,
                "user_id": fb.user_id,
                "session_id": fb.session_id,
                "name": fb.name,
                "age_range": fb.age_range,
                "interests": fb.interests,
                "rating": fb.rating,
                "liked_text": fb.liked_text,
                "liked_chips": fb.liked_chips,
                "disliked_text": fb.disliked_text,
                "disliked_chips": fb.disliked_chips,
                "additional_feedback": fb.additional_feedback,
                "submitted_at": fb.submitted_at.isoformat()
            }
            for fb in feedbacks
        ]
    finally:
        db.close()
