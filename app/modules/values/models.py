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

class Feedback(Base):
    """User feedback from values workshop"""
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    session_id = Column(String(255), nullable=True, index=True)  # link to values session if available
    
    # User info from init step 4
    name = Column(String(255), nullable=True)
    age_range = Column(String(100), nullable=True)  # e.g., "18-25", "26-35", etc.
    interests = Column(JSON, nullable=True)  # array of interests
    
    # Feedback form data
    rating = Column(Integer, nullable=True)  # 1-5 stars
    liked_text = Column(Text, nullable=True)  # free text about what they liked
    liked_chips = Column(JSON, nullable=True)  # selected chips for liked
    disliked_text = Column(Text, nullable=True)  # free text about what they didn't like
    disliked_chips = Column(JSON, nullable=True)  # selected chips for disliked
    additional_feedback = Column(Text, nullable=True)  # "Tell us more" section
    
    # Metadata
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String(45), nullable=True)  # for analytics (optional)
    user_agent = Column(Text, nullable=True)  # for analytics (optional)
