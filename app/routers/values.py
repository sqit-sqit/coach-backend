from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pathlib import Path
from . import service_init, schemas

router = APIRouter(tags=["values"])

# ---------- INIT (bez zmian) ----------

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

# ---------- SELECT (debug version) ----------

@router.get("/list")
def get_values():
    """
    Zwraca listę wartości z pliku data/value_list.txt
    """
    base_dir = Path(__file__).resolve().parents[3]
    file_path = base_dir / "data" / "value_list.txt"

    # 👀 Debug info w konsoli
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
