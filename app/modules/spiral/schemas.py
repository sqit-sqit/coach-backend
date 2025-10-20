# app/modules/spiral/schemas.py
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class SpiralSessionCreate(BaseModel):
    user_id: str
    initial_problem: Optional[str] = None

class SpiralSessionData(BaseModel):
    id: int
    user_id: str
    session_id: str
    initial_problem: Optional[str]
    current_cycle: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    status: str

class SpiralChatMessageCreate(BaseModel):
    session_id: str
    message: str
    cycle_number: Optional[int] = None
    question_type: Optional[str] = None

class SpiralChatMessage(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    cycle_number: Optional[int]
    question_type: Optional[str]
    is_summary: bool
    has_action_chips: bool
    created_at: datetime
    message_order: int

class SpiralChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict[str, Any]]] = []

class SpiralSummaryCreate(BaseModel):
    session_id: str
    summary_content: str
    insights: Optional[Dict[str, Any]] = None
    cycles_completed: int = 0

class SpiralSummary(BaseModel):
    id: int
    session_id: str
    summary_content: str
    insights: Optional[Dict[str, Any]]
    cycles_completed: int
    created_at: datetime

class SpiralSessionResponse(BaseModel):
    session: SpiralSessionData
    messages: List[SpiralChatMessage]
    summary: Optional[SpiralSummary] = None
