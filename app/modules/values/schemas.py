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
