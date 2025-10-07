# app/core/database.py
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Database URL - local development vs production
def get_database_url():
    """Get database URL based on environment"""
    if os.getenv("DATABASE_URL"):
        # Production (DigitalOcean) - PostgreSQL
        return os.getenv("DATABASE_URL")
    else:
        # Local development - SQLite
        return "sqlite:///./coach.db"

# Create engine
if os.getenv("DATABASE_URL"):
    # Production (PostgreSQL)
    engine = create_engine(
        get_database_url(),
        echo=True,  # Set to False in production
        pool_pre_ping=True,
        pool_recycle=300
    )
else:
    # Local development (SQLite)
    engine = create_engine(
        get_database_url(),
        echo=True,  # Set to False in production
        connect_args={"check_same_thread": False}  # SQLite specific
        # SQLite doesn't need pool_recycle
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Dependency to get database session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()