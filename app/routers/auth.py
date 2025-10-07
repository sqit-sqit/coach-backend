from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import RedirectResponse
from google.auth.transport import requests
from google.oauth2 import id_token
import os
from app.core.database import get_db
from app.core.models import User
from sqlalchemy.orm import Session
from jose import jwt
from datetime import datetime, timedelta
import requests as req
from typing import Optional

router = APIRouter()

# JWT Secret (w produkcji użyj bezpiecznego klucza)
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"

def create_access_token(user_id: str):
    """Tworzy JWT token dla użytkownika"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def get_current_user_from_token(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """Dependency do pobierania aktualnego użytkownika z Authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    try:
        # Usuń "Bearer " prefix jeśli istnieje
        token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
        
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/auth/google")
def google_auth():
    """Inicjalizuje logowanie przez Google"""
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
    
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={client_id}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid email profile&"
        f"access_type=offline"
    )
    
    return RedirectResponse(url=google_auth_url)

@router.get("/auth/google/callback")
def google_callback(code: str, db: Session = Depends(get_db)):
    """Obsługuje powrót z Google OAuth"""
    try:
        # Wymień kod na token
        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/auth/google/callback")
        
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }
        
        response = req.post(token_url, data=token_data)
        token_response = response.json()
        
        if "error" in token_response:
            raise HTTPException(status_code=400, detail=f"Google OAuth error: {token_response['error']}")
        
        # Pobierz dane użytkownika
        id_token_str = token_response.get("id_token")
        idinfo = id_token.verify_oauth2_token(id_token_str, requests.Request(), client_id)
        
        email = idinfo.get("email")
        name = idinfo.get("name")
        google_id = idinfo.get("sub")
        
        if not email:
            raise HTTPException(status_code=400, detail="No email provided by Google")
        
        # Znajdź lub utwórz użytkownika
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            user = User(
                user_id=google_id,
                email=email,
                name=name,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Aktualizuj user_id jeśli się zmienił
            if user.user_id != google_id:
                user.user_id = google_id
                db.commit()
        
        # Utwórz JWT token
        access_token = create_access_token(user.user_id)
        
        # Przekieruj do frontendu z tokenem
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        return RedirectResponse(f"{frontend_url}/auth/success?token={access_token}")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")

@router.get("/auth/me")
def get_current_user(token: str, db: Session = Depends(get_db)):
    """Pobiera dane aktualnego użytkownika"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/auth/logout")
def logout():
    """Wylogowanie użytkownika (frontend usuwa token)"""
    return {"message": "Logged out successfully"}