import json
import random
import time
from pathlib import Path
from typing import Any, Dict, Optional

from logic import BASE_ATK, BASE_DEFENSE, BASE_HP, BASE_MP, ORIGINS, birth_time_from_age, random_linh_can

DB_FILE = Path(__file__).with_name("thiendao.json")
_db: Dict[str, Any] = {"users": {}, "guilds": {}, "bi_canh": {"current": None}}


def _ensure_schema() -> None:
    _db.setdefault("users", {})
    _db.setdefault("guilds", {})
    _db.setdefault("bi_canh", {})
    _db["bi_canh"].setdefault("current", None)


def _migrate_user(user: Dict[str, Any]) -> Dict[str, Any]:
    now = int(time.time())
    origin = ORIGINS.get(user.get("origin_key", "phamnhan"), ORIGINS["phamnhan"])
    user.setdefault("origin_key", "phamnhan")
    user.setdefault("origin_name", origin["name"])
    user.setdefault("origin_lore", origin["lore"])
    user.setdefault("cong_phap_key", "")
    user.setdefault("cong_phap_name", "Chưa chọn")
    user.setdefault("linh_can", "Ngũ Linh Căn")
    user.setdefault("train_bonus", 0)
    user.setdefault("break_bonus", 0)
    user.setdefault("root_train_bonus", max(0, int(user.get("train_bonus", 0)) - int(origin["train_bonus"])))
    user.setdefault("root_break_bonus", max(0, int(user.get("break_bonus", 0)) - int(origin["break_bonus"])))
    user.setdefault("linh_thach", 0)
    user.setdefault("major_index", -1)
    user.setdefault("minor_stage", 0)
    user.setdefault("minor_cost", 10)
    user.setdefault("last_daily", 0)
    user.setdefault("created_at", now)
    user.setdefault("birth_time", birth_time_from_age(random.randint(12, 30), now))
    user.setdefault("hp", BASE_HP)
    user.setdefault("mp", BASE_MP)
    user.setdefault("atk", BASE_ATK)
    user.setdefault("defense", BASE_DEFENSE)
    user.setdefault("tu_vi", 0)
    user.setdefault("bag_items", {})
    user.setdefault("titles", [])
    user.setdefault("rebirth_count", 0)
    user.setdefault("y_canh_pieces", [])
    user.setdefault("in_bi_canh_id", "")
    user.setdefault("current_bi_canh_id", "")
    return user


def load_db() -> Dict[str, Any]:
    global _db
    if not DB_FILE.exists():
        save_db()
    try:
        _db = json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:
        _db = {"users": {}, "guilds": {}, "bi_canh": {"current": None}}
        save_db()
    _ensure_schema()
    users = _db.setdefault("users", {})
    for user_id, user in list(users.items()):
        users[user_id] = _migrate_user(user)
    return _db


def save_db() -> None:
    _ensure_schema()
    DB_FILE.write_text(json.dumps(_db, ensure_ascii=False, indent=2), encoding="utf-8")


def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    user = _db.setdefault("users", {}).get(str(user_id))
    if user:
        return _migrate_user(user)
    return None


def update_user(user_id: int, user: Dict[str, Any]) -> None:
    _db.setdefault("users", {})[str(user_id)] = _migrate_user(user)


def create_user(user_id: int, name: str, origin_key: str) -> Dict[str, Any]:
    from logic import ORIGINS, birth_time_from_age, random_linh_can

    origin = ORIGINS[origin_key]
    lc = random_linh_can()
    now = int(time.time())
    age = random.randint(12, 30)
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
        "root_train_bonus": lc["train_bonus"],
        "root_break_bonus": lc["break_bonus"],
        "linh_thach": origin["start_linh_thach"],
        "major_index": -1,
        "minor_stage": 0,
        "minor_cost": 10,
        "last_daily": 0,
        "created_at": now,
        "birth_time": birth_time_from_age(age, now),
        "hp": origin["hp"],
        "mp": origin["mp"],
        "atk": origin["atk"],
        "defense": origin["defense"],
        "tu_vi": 0,
        "bag_items": {},
        "titles": [],
        "rebirth_count": 0,
        "y_canh_pieces": [],
        "in_bi_canh_id": "",
        "current_bi_canh_id": "",
    }
    update_user(user_id, user)
    return user


def ensure_user(user_id: int, name: str, origin_key: str) -> Dict[str, Any]:
    user = get_user(user_id)
    if user:
        return user
    return create_user(user_id, name, origin_key)


def get_guild_config(guild_id: int) -> Dict[str, Any]:
    guilds = _db.setdefault("guilds", {})
    return guilds.setdefault(str(guild_id), {})


def set_guild_bicanh_channel(guild_id: int, channel_id: int) -> Dict[str, Any]:
    cfg = get_guild_config(guild_id)
    cfg["bi_canh_channel"] = int(channel_id)
    _db.setdefault("guilds", {})[str(guild_id)] = cfg
    return cfg


def get_guild_bicanh_channels() -> Dict[str, int]:
    result: Dict[str, int] = {}
    for guild_id, cfg in _db.setdefault("guilds", {}).items():
        channel_id = cfg.get("bi_canh_channel")
        if channel_id:
            result[guild_id] = int(channel_id)
    return result


def get_current_bi_canh() -> Optional[Dict[str, Any]]:
    return _db.setdefault("bi_canh", {}).get("current")


def set_current_bi_canh(event: Optional[Dict[str, Any]]) -> None:
    _db.setdefault("bi_canh", {})["current"] = event


def clear_current_bi_canh() -> None:
    _db.setdefault("bi_canh", {})["current"] = None


def set_user_in_bi_canh(user_id: int, event_id: str) -> None:
    user = get_user(user_id)
    if not user:
        return
    user["in_bi_canh_id"] = event_id
    user["current_bi_canh_id"] = event_id
    update_user(user_id, user)


def clear_users_from_bi_canh(event_id: str) -> None:
    users = _db.setdefault("users", {})
    for user_id, user in users.items():
        if user.get("in_bi_canh_id") == event_id or user.get("current_bi_canh_id") == event_id:
            user["in_bi_canh_id"] = ""
            user["current_bi_canh_id"] = ""
            users[user_id] = _migrate_user(user)
