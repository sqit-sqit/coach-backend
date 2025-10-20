# app/modules/spiral/service.py
from sqlalchemy.orm import Session
from app.modules.spiral.models import SpiralSession, SpiralChatMessage, SpiralSummary
from app.modules.spiral.schemas import SpiralChatMessageCreate
from typing import List, Optional
from datetime import datetime
from pathlib import Path
import os
from openai import OpenAI
from app.config.ai_models import get_model_config

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

    def add_ai_summary_message(self, session_id: str, content: str) -> SpiralChatMessage:
        """Add AI summary message (marked is_summary=True)"""
        last_message = self.db.query(SpiralChatMessage).filter(
            SpiralChatMessage.session_id == session_id
        ).order_by(SpiralChatMessage.message_order.desc()).first()

        next_order = (last_message.message_order + 1) if last_message else 1

        message = SpiralChatMessage(
            session_id=session_id,
            role="assistant",
            content=content,
            cycle_number=None,
            question_type=None,
            is_summary=True,
            has_action_chips=False,
            message_order=next_order
        )

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def generate_and_save_summary(self, session_id: str) -> str:
        """Generate a Polish summary for the spiral session and save it to DB and as an assistant message."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session not found")

        # If already has summary, return it
        existing = self.db.query(SpiralSummary).filter(SpiralSummary.session_id == session_id).first()
        if existing:
            return existing.summary_content

        # Build chat history text
        messages = self.get_session_messages(session_id)
        chat_text = ""
        for m in messages:
            role = "User" if m.role == "user" else "Assistant"
            chat_text += f"{role}: {m.content}\n"

        # Load summary prompt
        base_dir = Path(__file__).resolve().parents[2] / "personality"
        prompt_file = base_dir / "spiral_summary_prompt.pl.txt"
        if not prompt_file.exists():
            # Minimal fallback to avoid crashing
            prompt_template = (
                "Wygeneruj zwięzłe podsumowanie sesji Spiral po polsku na podstawie historii czatu.\n"
                "Problem początkowy: {initial_problem}\n"
                "Historia czatu:\n{chat_history}"
            )
        else:
            prompt_template = prompt_file.read_text(encoding="utf-8")

        final_prompt = (
            prompt_template
            .replace("{initial_problem}", session.initial_problem or "nie określono")
            .replace("{chat_history}", chat_text)
            .replace("{cycles_completed}", str(session.current_cycle or 0))
        )

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in .env")

        client = OpenAI(api_key=api_key)
        model_config = get_model_config("spiral_chat")

        messages_param = [
            {"role": "system", "content": "Wszystkie odpowiedzi udzielasz wyłącznie po polsku. Jesteś doświadczonym coachem podsumowującym sesję Spiral."},
            {"role": "user", "content": final_prompt}
        ]

        params = {
            "model": model_config["model"],
            "temperature": model_config["temperature"],
            "messages": messages_param
        }
        if model_config.get("max_tokens"):
            params["max_tokens"] = model_config["max_tokens"]

        completion = client.chat.completions.create(**params)
        summary_text = completion.choices[0].message.content

        # Save DB summary
        spiral_summary = SpiralSummary(
            session_id=session_id,
            summary_content=summary_text,
            insights=None,
            cycles_completed=session.current_cycle or 0
        )
        self.db.add(spiral_summary)
        self.db.commit()

        # Save as assistant message flagged as summary
        self.add_ai_summary_message(session_id, summary_text)

        # Optionally mark session completed
        # session.status = "completed"
        # session.ended_at = datetime.now()
        # self.db.commit()

        return summary_text
    
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
