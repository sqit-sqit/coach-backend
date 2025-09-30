# app/modules/values/service_init.py

USER_PROGRESS: dict[str, dict] = {}


def save_progress(user_id: str, phase: str, step: int, data: dict | None = None):
    """
    Zapisuje progres użytkownika dla danej fazy (init, select, reduce, choose...).
    """
    if user_id not in USER_PROGRESS:
        USER_PROGRESS[user_id] = {}

    USER_PROGRESS[user_id][phase] = {
        "step": step,
        "data": data or {}
    }

    print(">>> SAVE PROGRESS", user_id, phase, step, data)
    print(">>> FULL STORE", USER_PROGRESS)

    return {
        "user_id": user_id,
        "phase": phase,
        "step": step,
        "data": data or {}
    }


def get_progress(user_id: str, phase: str | None = None):
    """
    Pobiera progres użytkownika:
      - jeśli podasz phase (np. "select"), to zwróci dane tylko z tej fazy
      - jeśli nie podasz, zwróci całość.
    """
    print(">>> GET PROGRESS for", user_id, "phase:", phase)
    user_data = USER_PROGRESS.get(user_id, {})
    if phase:
        return user_data.get(phase, {"step": None, "data": {}})
    return user_data


# -----------------------------
#  HELPERY DLA POSZCZEGÓLNYCH FAZ
# -----------------------------

def save_selected_values(user_id: str, values: list[str]):
    """
    Zapisuje wartości z fazy SELECT.
    """
    return save_progress(user_id, "select", 1, {"selected_values": values})


def get_selected_values(user_id: str) -> list[str]:
    """
    Pobiera wartości z fazy SELECT.
    """
    return get_progress(user_id, "select").get("data", {}).get("selected_values", [])


def save_reduced_values(user_id: str, values: list[str]):
    """
    Zapisuje wartości z fazy REDUCE.
    """
    return save_progress(user_id, "reduce", 1, {"reduced_values": values})


def get_reduced_values(user_id: str) -> list[str]:
    """
    Pobiera wartości z fazy REDUCE.
    """
    return get_progress(user_id, "reduce").get("data", {}).get("reduced_values", [])


def save_chosen_value(user_id: str, value: str):
    """
    Zapisuje pojedynczą wybraną wartość w fazie CHOOSE.
    """
    return save_progress(user_id, "choose", 1, {"chosen_value": value})


def get_chosen_value(user_id: str) -> str | None:
    """
    Pobiera wybraną wartość z fazy CHOOSE.
    """
    return get_progress(user_id, "choose").get("data", {}).get("chosen_value")


# Game

def save_top_value(user_id: str, value: str):
    if user_id not in USER_PROGRESS:
        USER_PROGRESS[user_id] = {}

    USER_PROGRESS[user_id]["game"] = {"top_value": value}

    print(f">>> TOP VALUE for {user_id}: {value}")
    return {"user_id": user_id, "top_value": value}
