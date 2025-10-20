# app/modules/values/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from app.core.database import Base
from app.core.models import Feedback

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
    summary = relationship("ValuesSummary", uselist=False, back_populates="session")
    
    feedback = relationship(
        "Feedback",
        primaryjoin="and_(ValuesSession.session_id==Feedback.session_id, Feedback.module=='values')",
        uselist=False,
        foreign_keys="[Feedback.session_id]"
    )

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

# This model is now obsolete and replaced by the generic Feedback model in app/core/models.py
# class Feedback(Base):
#     __tablename__ = 'feedback'

#     id = Column(Integer, primary_key=True, index=True)
#     user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
#     session_id = Column(String, ForeignKey('values_sessions.session_id'), nullable=False)
#     rating = Column(Integer)
#     liked_text = Column(String)
#     liked_chips = Column(JSON)
#     disliked_text = Column(String)
#     disliked_chips = Column(JSON)
#     additional_feedback = Column(String)
#     created_at = Column(DateTime, server_default=func.now())

#     user = relationship("User")
#     session = relationship("ValuesSession", back_populates="feedback")
