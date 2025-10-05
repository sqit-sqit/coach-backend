from fastapi import APIRouter
from fastapi.responses import JSONResponse, StreamingResponse
from pathlib import Path
from pydantic import BaseModel
from . import service_init, schemas

router = APIRouter(tags=["values"])

# ---------- INIT ----------
@router.post("/init/progress")
def update_progress(progress: schemas.InitProgress):
    return service_init.save_progress(
        user_id=progress.user_id,
        phase=progress.phase,
        step=progress.step,
        data=progress.data.dict() if progress.data else None
    )

@router.get("/init/progress/{user_id}")
def read_progress(user_id: str):
    return service_init.get_progress(user_id)

# ---------- SELECT ----------
@router.post("/select")
def save_selected(progress: schemas.ValuesSelect):
    return service_init.save_selected_values(progress.user_id, progress.selected_values)

@router.get("/select/{user_id}")
def get_selected(user_id: str):
    return {"selected_values": service_init.get_selected_values(user_id)}

# ---------- REDUCE ----------
@router.post("/reduce")
def save_reduced(progress: schemas.ValuesReduce):
    return service_init.save_reduced_values(progress.user_id, progress.reduced_values)

@router.get("/reduce/{user_id}")
def get_reduced(user_id: str):
    return {"reduced_values": service_init.get_reduced_values(user_id)}

# ---------- CHOOSE ----------
@router.post("/choose")
def save_chosen(progress: schemas.ValuesChoose):
    return service_init.save_chosen_value(progress.user_id, progress.chosen_value)

@router.get("/choose/{user_id}")
def get_chosen(user_id: str):
    return {"chosen_value": service_init.get_chosen_value(user_id)}

# ---------- VALUES LIST ----------
@router.get("/list")
def get_values():
    """
    Zwraca listę wartości z pliku data/value_list.txt
    """
    base_dir = Path(__file__).resolve().parents[3]
    file_path = base_dir / "data" / "value_list.txt"

    print(">>> [values/list] Looking for file:", file_path)

    if not file_path.exists():
        msg = f"File not found: {file_path}"
        print(">>> [values/list] ERROR:", msg)
        return JSONResponse({"error": msg}, status_code=404)

    try:
        with file_path.open("r", encoding="utf-8") as f:
            values = [line.strip() for line in f if line.strip()]
        print(f">>> [values/list] Loaded {len(values)} values from file.")
        return JSONResponse(values)
    except Exception as e:
        msg = f"Error reading file {file_path}: {e}"
        print(">>> [values/list] ERROR:", msg)
        return JSONResponse({"error": msg}, status_code=500)

# ---------- GAME ----------
@router.post("/game/{user_id}")
def save_game_value(user_id: str, value: dict):
    return service_init.save_top_value(user_id, value["top_value"])

# ---------- CHAT ----------
# Import service_chat if it exists, otherwise create simple fallback
try:
    from .service_chat import chat_with_ai, stream_chat_with_ai
    CHAT_AVAILABLE = True
except ImportError:
    CHAT_AVAILABLE = False
    print("⚠️ Warning: service_chat.py not found - chat endpoints disabled")

class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []

if CHAT_AVAILABLE:
    @router.post("/chat/{user_id}")
    def chat_endpoint(user_id: str, req: ChatRequest):
        """
        Endpoint chatu z AI.
        """
        response = chat_with_ai(
            user_message=req.message,
            history=req.history
        )
        return {"reply": response}

    @router.post("/chat/{user_id}/stream")
    def chat_stream_endpoint(user_id: str, req: ChatRequest):
        """
        Streamingowy endpoint chatu z AI. Zwraca strumień tekstu.
        """
        generator = stream_chat_with_ai(
            user_message=req.message,
            history=req.history
        )
        return StreamingResponse(generator, media_type="text/plain; charset=utf-8")
else:
    @router.post("/chat/{user_id}")
    def chat_endpoint_disabled(user_id: str, req: ChatRequest):
        return {"error": "Chat service not available"}

    @router.post("/chat/{user_id}/stream")
    def chat_stream_endpoint_disabled(user_id: str, req: ChatRequest):
        return {"error": "Chat service not available"}