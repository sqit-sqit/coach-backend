# app/core/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    """Central user table for all mini-apps"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True, nullable=False)  # demo-user-123
    email = Column(String(255), unique=True, index=True, nullable=True)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user_apps = relationship("UserApp", back_populates="user")
    app_sessions = relationship("AppSession", back_populates="user")

class UserApp(Base):
    """Track which mini-apps user has used"""
    __tablename__ = "user_apps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    app_name = Column(String(50), nullable=False)  # 'values', 'grow', etc.
    first_used_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), onupdate=func.now())
    usage_count = Column(Integer, default=1)
    
    # Relationships
    user = relationship("User", back_populates="user_apps")

class AppSession(Base):
    """Track sessions across all mini-apps"""
    __tablename__ = "app_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), ForeignKey("users.user_id"), nullable=False)
    app_name = Column(String(50), nullable=False)  # 'values', 'grow', etc.
    session_id = Column(String(255), nullable=False)  # unique session identifier
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), default="active")  # 'active', 'completed', 'abandoned'
    session_data = Column(JSON, nullable=True)  # flexible data for different apps - RENAMED FROM metadata
    
    # Relationships
    user = relationship("User", back_populates="app_sessions")