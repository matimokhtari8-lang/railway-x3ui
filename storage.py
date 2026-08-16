import json
import os
import threading

_LOCK = threading.Lock()
_FILE = os.environ.get("STORAGE_FILE", "/data/configs.json")


def _load() -> dict:
    if not os.path.exists(_FILE):
        return {}
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict):
    os.makedirs(os.path.dirname(_FILE), exist_ok=True)
    with open(_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_config(user_id: int, entry: dict):
    with _LOCK:
        data = _load()
        data.setdefault(str(user_id), []).append(entry)
        _save(data)


def get_configs(user_id: int) -> list:
    with _LOCK:
        data = _load()
        return data.get(str(user_id), [])


def total_count() -> int:
    with _LOCK:
        data = _load()
        return sum(len(v) for v in data.values())
