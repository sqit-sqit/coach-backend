# app/modules/spiral/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SpiralSession(Base):
    """Spiral reflection session"""
    __tablename__ = "spiral_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    initial_problem = Column(Text, nullable=True)  # The problem/challenge user wants to explore
    current_cycle = Column(Integer, default=1)  # Which cycle they're in (1, 2, 3, etc.)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")  # 'active', 'completed'
    
    # Relationships
    user = relationship("User", back_populates="spiral_sessions")
    chat_messages = relationship("SpiralChatMessage", back_populates="session", cascade="all, delete-orphan")
    summary = relationship("SpiralSummary", back_populates="session", uselist=False)

class SpiralChatMessage(Base):
    """Individual chat messages in spiral session"""
    __tablename__ = "spiral_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("spiral_sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    cycle_number = Column(Integer, nullable=True)  # Which cycle this message belongs to
    question_type = Column(String(50), nullable=True)  # 'who_am_i', 'what_do_i_do', 'what_do_i_have'
    is_summary = Column(Boolean, default=False)
    has_action_chips = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message_order = Column(Integer, nullable=False)  # order in conversation
    
    # Relationships
    session = relationship("SpiralSession", back_populates="chat_messages")

class SpiralSummary(Base):
    """Generated summaries for spiral sessions"""
    __tablename__ = "spiral_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("spiral_sessions.session_id"), nullable=False, unique=True)
    summary_content = Column(Text, nullable=False)
    insights = Column(JSON, nullable=True)  # Key insights discovered
    cycles_completed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("SpiralSession", back_populates="summary")

