# app/modules/values/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ValuesSession(Base):
    """Values exploration session"""
    __tablename__ = "values_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    chosen_value = Column(String(255), nullable=True)
    chat_mode = Column(String(20), default="chat")  # 'chat' or 'reflect'
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")  # 'active', 'completed'
    
    # Relationships
    chat_messages = relationship("ValuesChatMessage", back_populates="session", cascade="all, delete-orphan")
    summary = relationship("ValuesSummary", back_populates="session", uselist=False)

class ValuesChatMessage(Base):
    """Individual chat messages in values session"""
    __tablename__ = "values_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("values_sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    is_summary = Column(Boolean, default=False)
    has_action_chips = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message_order = Column(Integer, nullable=False)  # order in conversation
    
    # Relationships
    session = relationship("ValuesSession", back_populates="chat_messages")

class ValuesSummary(Base):
    """Generated summaries for values sessions"""
    __tablename__ = "values_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("values_sessions.session_id"), nullable=False, unique=True)
    summary_content = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_history = Column(JSON, nullable=True)  # chat phase history
    reflection_history = Column(JSON, nullable=True)  # reflection phase history
    
    # Relationships
    session = relationship("ValuesSession", back_populates="summary")
