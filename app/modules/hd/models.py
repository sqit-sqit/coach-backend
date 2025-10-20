# app/modules/hd/models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class HDSession(Base):
    """Human Design session"""
    __tablename__ = "hd_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    session_id = Column(String(255), nullable=False, unique=True, index=True)
    
    # Birth data
    name = Column(String(255), nullable=False)
    birth_date = Column(DateTime, nullable=False)
    birth_time = Column(String(10), nullable=False)  # "14:30"
    birth_place = Column(String(255), nullable=False)
    birth_lat = Column(Float, nullable=False)
    birth_lng = Column(Float, nullable=False)
    
    # Calculation system settings
    zodiac_system = Column(String(20), default="sidereal")  # "tropical" or "sidereal"
    calculation_method = Column(String(20), default="degrees")  # "days" or "degrees"
    
    # Human Design results
    type = Column(String(50), nullable=False)  # "Generator", "Manifestor", "Projector", "Reflector"
    strategy = Column(String(100), nullable=False)  # "To Respond", "To Inform", etc.
    authority = Column(String(100), nullable=False)  # "Sacral", "Solar Plexus", etc.
    profile = Column(String(10), nullable=False)  # "1/3", "2/4", etc.
    
    # Chart data (gates)
    sun_gate = Column(Integer, nullable=False)
    earth_gate = Column(Integer, nullable=False)
    moon_gate = Column(Integer, nullable=False)
    north_node_gate = Column(Integer, nullable=False)
    south_node_gate = Column(Integer, nullable=False)
    
    # Centers (defined/undefined)
    defined_centers = Column(JSON, nullable=True)  # List of defined centers
    undefined_centers = Column(JSON, nullable=True)  # List of undefined centers
    
    # Channels (defined channels)
    defined_channels = Column(JSON, nullable=True)  # List of defined channels

    # Gates (active gates from both personality and design)
    active_gates = Column(JSON, nullable=True)  # List of active gates
    # Full planetary activations [{side, planet, lon, gate, line}]
    activations = Column(JSON, nullable=True)
    
    # Session metadata
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")  # 'active', 'completed'
    
    # Relationships
    user = relationship("User", back_populates="hd_sessions")
    chat_messages = relationship("HDChatMessage", back_populates="session", cascade="all, delete-orphan")
    summary = relationship("HDSummary", back_populates="session", uselist=False)

class HDChatMessage(Base):
    """Individual chat messages in HD session"""
    __tablename__ = "hd_chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("hd_sessions.session_id"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    is_summary = Column(Boolean, default=False)
    has_action_chips = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    message_order = Column(Integer, nullable=False)  # order in conversation
    
    # Relationships
    session = relationship("HDSession", back_populates="chat_messages")

class HDSummary(Base):
    """Generated summaries for HD sessions"""
    __tablename__ = "hd_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), ForeignKey("hd_sessions.session_id"), nullable=False, unique=True)
    summary_content = Column(Text, nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    chat_history = Column(JSON, nullable=True)  # chat phase history
    
    # Relationships
    session = relationship("HDSession", back_populates="summary")
