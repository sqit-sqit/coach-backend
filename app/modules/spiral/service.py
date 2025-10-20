# app/modules/spiral/service.py
from sqlalchemy.orm import Session
from app.modules.spiral.models import SpiralSession, SpiralChatMessage, SpiralSummary
from app.modules.spiral.schemas import SpiralChatMessageCreate
from typing import List, Optional
from datetime import datetime

class SpiralService:
    """Service for managing spiral reflection sessions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, user_id: str, initial_problem: Optional[str] = None) -> SpiralSession:
        """Create a new spiral session"""
        session_id = f"{user_id}-spiral-{int(datetime.now().timestamp())}"
        
        session = SpiralSession(
            user_id=user_id,
            session_id=session_id,
            initial_problem=initial_problem,
            current_cycle=1,
            status="active"
        )
        
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[SpiralSession]:
        """Get spiral session by ID"""
        return self.db.query(SpiralSession).filter(
            SpiralSession.session_id == session_id
        ).first()
    
    def get_session_messages(self, session_id: str) -> List[SpiralChatMessage]:
        """Get all messages for a session"""
        return self.db.query(SpiralChatMessage).filter(
            SpiralChatMessage.session_id == session_id
        ).order_by(SpiralChatMessage.message_order).all()
    
    def add_message(self, message_data: SpiralChatMessageCreate) -> SpiralChatMessage:
        """Add a new message to the session"""
        # Get next message order
        last_message = self.db.query(SpiralChatMessage).filter(
            SpiralChatMessage.session_id == message_data.session_id
        ).order_by(SpiralChatMessage.message_order.desc()).first()
        
        next_order = (last_message.message_order + 1) if last_message else 1
        
        message = SpiralChatMessage(
            session_id=message_data.session_id,
            role="user",
            content=message_data.message,
            cycle_number=message_data.cycle_number,
            question_type=message_data.question_type,
            message_order=next_order
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def add_ai_message(self, session_id: str, content: str, cycle_number: Optional[int] = None) -> SpiralChatMessage:
        """Add AI response message"""
        # Get next message order
        last_message = self.db.query(SpiralChatMessage).filter(
            SpiralChatMessage.session_id == session_id
        ).order_by(SpiralChatMessage.message_order.desc()).first()
        
        next_order = (last_message.message_order + 1) if last_message else 1
        
        message = SpiralChatMessage(
            session_id=session_id,
            role="assistant",
            content=content,
            cycle_number=cycle_number,
            message_order=next_order
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def update_session_cycle(self, session_id: str, new_cycle: int):
        """Update the current cycle for a session"""
        session = self.get_session(session_id)
        if session:
            session.current_cycle = new_cycle
            self.db.commit()
    
    def complete_session(self, session_id: str):
        """Mark session as completed"""
        session = self.get_session(session_id)
        if session:
            session.status = "completed"
            session.ended_at = datetime.now()
            self.db.commit()
