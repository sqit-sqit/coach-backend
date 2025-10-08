# app/modules/values/schemas.py
from pydantic import BaseModel
from typing import List, Optional

# --- INIT ---
class InitData(BaseModel):
    name: Optional[str] = None
    age_range: Optional[str] = None
    interests: List[str] = []

class InitProgress(BaseModel):
    user_id: str
    phase: str
    step: int
    data: Optional[InitData] = None


# --- SELECT ---
class ValuesSelect(BaseModel):
    user_id: str
    selected_values: List[str]


# --- REDUCE ---
class ValuesReduce(BaseModel):
    user_id: str
    reduced_values: List[str]


# --- CHOOSE ---
class ValuesChoose(BaseModel):
    user_id: str
    chosen_value: str


# --- FEEDBACK ---
class FeedbackSubmit(BaseModel):
    user_id: str
    session_id: Optional[str] = None
    
    # User info (from init step 4)
    name: Optional[str] = None
    age_range: Optional[str] = None
    interests: Optional[List[str]] = []
    
    # Feedback form data
    rating: Optional[int] = None
    liked_text: Optional[str] = None
    liked_chips: Optional[List[str]] = []
    disliked_text: Optional[str] = None
    disliked_chips: Optional[List[str]] = []
    additional_feedback: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    user_id: str
    session_id: Optional[str]
    name: Optional[str]
    age_range: Optional[str]
    interests: Optional[List[str]]
    rating: Optional[int]
    liked_text: Optional[str]
    liked_chips: Optional[List[str]]
    disliked_text: Optional[str]
    disliked_chips: Optional[List[str]]
    additional_feedback: Optional[str]
    submitted_at: str
