from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.database import get_db
from app.core.models import Feedback, User

router = APIRouter()

class FeedbackCreate(BaseModel):
    user_id: str
    rating: int
    liked_text: Optional[str] = None
    liked_chips: Optional[List[str]] = None
    disliked_text: Optional[str] = None
    disliked_chips: Optional[List[str]] = None
    additional_feedback: Optional[str] = None
    module: str
    session_id: Optional[str] = None

@router.post("/")
async def submit_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """Submit feedback for any module"""
    try:
        # Check if user exists
        user = db.query(User).filter(User.user_id == feedback_data.user_id).first()
        if not user and not feedback_data.user_id.startswith("guest-"):
             raise HTTPException(status_code=404, detail="User not found")

        db_feedback = Feedback(
            user_id=feedback_data.user_id,
            rating=feedback_data.rating,
            liked_text=feedback_data.liked_text,
            liked_chips=feedback_data.liked_chips,
            disliked_text=feedback_data.disliked_text,
            disliked_chips=feedback_data.disliked_chips,
            additional_feedback=feedback_data.additional_feedback,
            module=feedback_data.module,
            session_id=feedback_data.session_id
        )
        db.add(db_feedback)
        db.commit()
        db.refresh(db_feedback)
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")
