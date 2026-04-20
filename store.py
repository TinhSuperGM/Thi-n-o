import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

DB_FILE = Path(__file__).with_name("thiendao.json")
_db: Dict[str, Any] = {"users": {}}


def load_db() -> Dict[str, Any]:
    global _db
    if not DB_FILE.exists():
        save_db()
    try:
        _db = json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:
        _db = {"users": {}}
        save_db()
    if "users" not in _db:
        _db["users"] = {}
    return _db


def save_db() -> None:
    DB_FILE.write_text(json.dumps(_db, ensure_ascii=False, indent=2), encoding="utf-8")


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    return _db.setdefault("users", {}).get(str(user_id))


def update_user(user_id: int, user: Dict[str, Any]) -> None:
    _db.setdefault("users", {})[str(user_id)] = user


def create_user(user_id: int, name: str, origin_key: str) -> Dict[str, Any]:
    from logic import ORIGINS, random_linh_can

    origin = ORIGINS[origin_key]
    lc = random_linh_can()
    user = {
        "name": name,
        "origin_key": origin_key,
        "origin_name": origin["name"],
        "origin_lore": origin["lore"],
        "cong_phap_key": "",
        "cong_phap_name": "Chưa chọn",
        "linh_can": lc["name"],
        "train_bonus": lc["train_bonus"] + origin["train_bonus"],
        "break_bonus": lc["break_bonus"] + origin["break_bonus"],
        "linh_thach": origin["start_linh_thach"],
        "major_index": -1,
        "minor_stage": 0,
        "minor_cost": 10,
        "last_daily": 0,
        "created_at": int(time.time()),
        "hp": origin["hp"],
        "mp": origin["mp"],
        "atk": origin["atk"],
        "defense": origin["defense"],
        "tu_vi": 0,
    }
    update_user(user_id, user)
    return user


def ensure_user(user_id: int, name: str, origin_key: str) -> Dict[str, Any]:
    user = get_user(user_id)
    if user:
        return user
    return create_user(user_id, name, origin_key)
