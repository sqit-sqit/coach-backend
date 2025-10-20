# app/modules/spiral/router.py
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.spiral.models import SpiralSession, SpiralChatMessage as SpiralChatMessageModel, SpiralSummary
from app.modules.spiral.schemas import (
    SpiralSessionCreate, SpiralSessionResponse, SpiralChatRequest,
    SpiralChatMessage, SpiralSummaryCreate, SpiralSessionData
)
from app.modules.spiral.service import SpiralService
from app.modules.spiral import chat_router
import uuid
from datetime import datetime

router = APIRouter()

# Include chat router
router.include_router(chat_router.router)

@router.post("/sessions", response_model=SpiralSessionResponse)
async def create_spiral_session(
    session_data: SpiralSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new spiral reflection session"""
    try:
        # Generate unique session ID
        session_id = f"{session_data.user_id}-spiral-{int(datetime.now().timestamp())}"
        
        # Create session
        db_session = SpiralSession(
            user_id=session_data.user_id,
            session_id=session_id,
            initial_problem=session_data.initial_problem,
            current_cycle=1,
            status="active"
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return SpiralSessionResponse(
            session=SpiralSessionData(
                id=db_session.id,
                user_id=db_session.user_id,
                session_id=db_session.session_id,
                initial_problem=db_session.initial_problem,
                current_cycle=db_session.current_cycle,
                started_at=db_session.started_at,
                ended_at=db_session.ended_at,
                status=db_session.status
            ),
            messages=[],
            summary=None
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating spiral session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=SpiralSessionResponse)
async def get_spiral_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Get spiral session with messages and summary"""
    try:
        # Get session
        session = db.query(SpiralSession).filter(SpiralSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Spiral session not found")
        
        # Get messages
        messages = db.query(SpiralChatMessageModel).filter(
            SpiralChatMessageModel.session_id == session_id
        ).order_by(SpiralChatMessageModel.message_order).all()
        
        # Get summary if exists
        summary = db.query(SpiralSummary).filter(
            SpiralSummary.session_id == session_id
        ).first()
        
        return SpiralSessionResponse(
            session=SpiralSessionData(
                id=session.id,
                user_id=session.user_id,
                session_id=session.session_id,
                initial_problem=session.initial_problem,
                current_cycle=session.current_cycle,
                started_at=session.started_at,
                ended_at=session.ended_at,
                status=session.status
            ),
            messages=[SpiralChatMessage(
                id=msg.id,
                session_id=msg.session_id,
                role=msg.role,
                content=msg.content,
                cycle_number=msg.cycle_number,
                question_type=msg.question_type,
                is_summary=msg.is_summary,
                has_action_chips=msg.has_action_chips,
                created_at=msg.created_at,
                message_order=msg.message_order
            ) for msg in messages],
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving spiral session: {str(e)}")

@router.get("/sessions/user/{user_id}")
async def get_user_spiral_sessions(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Get all spiral sessions for a user"""
    try:
        sessions = db.query(SpiralSession).filter(
            SpiralSession.user_id == user_id
        ).order_by(SpiralSession.started_at.desc()).all()
        
        return {"sessions": sessions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving user sessions: {str(e)}")

@router.post("/sessions/{session_id}/complete")
async def complete_spiral_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Mark spiral session as completed"""
    try:
        session = db.query(SpiralSession).filter(SpiralSession.session_id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Spiral session not found")
        
        session.status = "completed"
        session.ended_at = datetime.now()
        
        db.commit()
        
        return {"message": "Session completed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error completing session: {str(e)}")
