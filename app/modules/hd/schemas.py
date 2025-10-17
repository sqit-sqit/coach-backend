# app/modules/hd/schemas.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# --- INIT ---
class HDInitData(BaseModel):
    name: str
    birth_date: datetime
    birth_time: str  # "14:30"
    birth_place: str
    birth_lat: float
    birth_lng: float

class HDInitProgress(BaseModel):
    user_id: str
    phase: str
    step: int
    data: Optional[HDInitData] = None

# --- CHART CALCULATION ---
class HDChartRequest(BaseModel):
    user_id: str
    name: str
    birth_date: datetime
    birth_time: str
    birth_place: str
    birth_lat: float
    birth_lng: float
    # System obliczeń
    zodiac_system: str = "tropical"  # "tropical" or "sidereal"
    calculation_method: str = "degrees"  # "days" or "degrees"

class HDChartResponse(BaseModel):
    session_id: str
    type: str
    strategy: str
    authority: str
    profile: str
    sun_gate: int
    earth_gate: int
    moon_gate: int
    north_node_gate: int
    south_node_gate: int
    defined_centers: List[str]
    undefined_centers: List[str]
    defined_channels: List[str]
    active_gates: List[int]
    # Planetary activations grouped by side
    activations: List[dict] | None = None

# --- CHAT ---
class HDChatMessage(BaseModel):
    session_id: str
    message: str

class HDChatResponse(BaseModel):
    response: str
    message_id: str
    has_action_chips: bool = False

# --- SUMMARY ---
class HDSummaryRequest(BaseModel):
    session_id: str

class HDSummaryResponse(BaseModel):
    summary: str
    generated_at: str

# --- SESSION DATA ---
class HDSessionData(BaseModel):
    session_id: str
    user_id: str
    name: str
    birth_date: datetime
    birth_time: str
    birth_place: str
    birth_lat: float
    birth_lng: float
    zodiac_system: str
    calculation_method: str
    type: str
    strategy: str
    authority: str
    profile: str
    sun_gate: int
    earth_gate: int
    moon_gate: int
    north_node_gate: int
    south_node_gate: int
    defined_centers: List[str]
    undefined_centers: List[str]
    defined_channels: List[str]
    active_gates: List[int]
    activations: List[dict] | None = None
    status: str
    started_at: str
    ended_at: Optional[str] = None

# --- CHAT HISTORY ---
class HDChatHistory(BaseModel):
    session_id: str
    messages: List[dict]
    total_messages: int
