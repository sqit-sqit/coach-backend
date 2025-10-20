# app/modules/spiral/service_chat.py
from app.core.chat_service import BaseChatService
from app.modules.spiral.models import SpiralSession, SpiralChatMessage
from app.modules.spiral.schemas import SpiralChatRequest
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os

class SpiralChatService(BaseChatService):
    """Specialized chat service for Spiral reflection sessions"""
    
    def __init__(self, db: Session):
        super().__init__("spiral")
        self.db = db
    
    def load_spiral_personality(self, session_id: str) -> str:
        """Load spiral personality with session context"""
        try:
            # Get session data
            session = self.db.query(SpiralSession).filter(
                SpiralSession.session_id == session_id
            ).first()
            
            if not session:
                return self._load_personality("spiral_personality_chat.txt")
            
            # Load base personality
            personality = self._load_personality("spiral_personality_chat.txt")
            
            # Add session context
            context = f"""
            
User's Spiral Session Context:
- Initial Problem: {session.initial_problem or 'Not specified'}
- Current Cycle: {session.current_cycle}
- Session Status: {session.status}
- Session Started: {session.started_at}

Use this context to guide the spiral reflection process appropriately.
"""
            
            return personality + context
            
        except Exception as e:
            print(f"Error loading spiral personality: {e}")
            return self._load_personality("spiral_personality_chat.txt")
    
    def get_chat_history(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get chat history for spiral session"""
        try:
            messages = self.db.query(SpiralChatMessage).filter(
                SpiralChatMessage.session_id == session_id
            ).order_by(SpiralChatMessage.message_order.desc()).limit(limit).all()
            
            # Convert to chat format and reverse order
            history = []
            for msg in reversed(messages):
                if not msg.is_summary:  # Exclude summaries from chat history
                    history.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            return history
            
        except Exception as e:
            print(f"Error getting spiral chat history: {e}")
            return []
    
    def save_user_message(self, session_id: str, message: str, cycle_number: int = None, question_type: str = None) -> SpiralChatMessage:
        """Save user message to spiral session"""
        try:
            # Get next message order
            last_message = self.db.query(SpiralChatMessage).filter(
                SpiralChatMessage.session_id == session_id
            ).order_by(SpiralChatMessage.message_order.desc()).first()
            
            next_order = (last_message.message_order + 1) if last_message else 1
            
            user_message = SpiralChatMessage(
                session_id=session_id,
                role="user",
                content=message,
                cycle_number=cycle_number,
                question_type=question_type,
                message_order=next_order
            )
            
            self.db.add(user_message)
            self.db.commit()
            self.db.refresh(user_message)
            
            return user_message
            
        except Exception as e:
            self.db.rollback()
            print(f"Error saving spiral user message: {e}")
            raise
    
    def save_ai_message(self, session_id: str, content: str, cycle_number: int = None) -> SpiralChatMessage:
        """Save AI response to spiral session"""
        try:
            # Get next message order
            last_message = self.db.query(SpiralChatMessage).filter(
                SpiralChatMessage.session_id == session_id
            ).order_by(SpiralChatMessage.message_order.desc()).first()
            
            next_order = (last_message.message_order + 1) if last_message else 1
            
            ai_message = SpiralChatMessage(
                session_id=session_id,
                role="assistant",
                content=content,
                cycle_number=cycle_number,
                message_order=next_order
            )
            
            self.db.add(ai_message)
            self.db.commit()
            self.db.refresh(ai_message)
            
            return ai_message
            
        except Exception as e:
            self.db.rollback()
            print(f"Error saving spiral AI message: {e}")
            raise
    
    def get_model_config(self) -> Dict[str, Any]:
        """Get AI model configuration for spiral chat"""
        return self._get_model_config("spiral_chat")
    
    def _load_personality(self, context_data: Dict[str, Any]) -> str:
        """Load personality from file with context data"""
        try:
            personality_path = os.path.join("app", "personality", "spiral_personality_chat.txt")
            with open(personality_path, "r", encoding="utf-8") as f:
                personality_template = f.read()
            
            # Format personality with context data
            return personality_template.format(
                initial_problem=context_data.get("initial_problem", "not specified"),
                current_cycle=context_data.get("current_cycle", 1)
            )
        except Exception as e:
            print(f"Error loading personality file: {e}")
            return "You are a helpful AI assistant for spiral reflection."
    
    def _get_start_message(self) -> str:
        """Get the initial message for spiral chat"""
        return "Rozpocznij spiralną refleksję. Zapytaj mnie, jaki problem, wyzwanie lub emocję chciałbym zgłębić."
