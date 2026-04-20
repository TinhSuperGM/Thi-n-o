import math
import random
import time
from typing import Any, Dict, List, Optional, Tuple

MINOR_STAGES = ["Sơ Kỳ", "Trung Kỳ", "Hậu Kỳ", "Viên Mãn"]

MAJOR_REALMS = [
    "Luyện Khí",
    "Trúc Cơ",
    "Kết Đan",
    "Nguyên Anh",
    "Hoá Thần",
    "Anh Biến",
    "Vấn Đỉnh",
    "Âm Hư Dương Thực",
    "Khuy Niết",
    "Tịnh Niết",
    "Toái Niết",
    "Thiên Nhân Ngũ Suy",
]

BREAKTHROUGH_RATES = {
    0: 70,
    1: 65,
    2: 60,
    3: 55,
    4: 50,
    5: 45,
    6: 40,
    7: 35,
    8: 30,
    9: 25,
    10: 20,
    11: 5,
}

LINH_CAN = [
    {"name": "Ngũ Linh Căn", "rate": 40, "train_bonus": 5, "break_bonus": 5},
    {"name": "Tứ Linh Căn", "rate": 25, "train_bonus": 15, "break_bonus": 10},
    {"name": "Tam Linh Căn", "rate": 18, "train_bonus": 10, "break_bonus": 12},
    {"name": "Biến Linh Căn", "rate": 10, "train_bonus": 20, "break_bonus": 15},
    {"name": "Thiên Linh Căn", "rate": 5, "train_bonus": 35, "break_bonus": 20},
    {"name": "Lôi Linh Căn", "rate": 0.4, "train_bonus": 50, "break_bonus": 35},
    {"name": "Băng Linh Căn", "rate": 0.4, "train_bonus": 50, "break_bonus": 35},
    {"name": "Huyền Âm Linh Căn", "rate": 0.4, "train_bonus": 50, "break_bonus": 35},
    {"name": "Không Gian Linh Căn", "rate": 0.4, "train_bonus": 50, "break_bonus": 35},
    {"name": "Hỗn Độn Linh Căn", "rate": 0.4, "train_bonus": 50, "break_bonus": 35},
]

ORIGINS = {
    "phesvat": {
        "name": "Phế Vật Nghịch Thiên",
        "lore": "Ngươi vốn bị xem thường, kinh mạch tắc nghẽn, tư chất bình thường. Thế nhưng trong một lần tuyệt vọng, ngươi vô tình chạm vào một cơ duyên cổ xưa...",
        "aliases": ["phesvat", "phevat", "phếvật", "phế-vật"],
        "start_linh_thach": 0,
        "hp": 100,
        "mp": 50,
        "atk": 5,
        "defense": 5,
        "train_bonus": 8,
        "break_bonus": 8,
    },
    "giatoc": {
        "name": "Gia Tộc Biến Cố",
        "lore": "Một đêm mưa máu, gia tộc ngươi bị diệt môn. Ngươi mang theo mối thù và một phần gia bảo, bắt đầu con đường phục hận.",
        "aliases": ["giatoc", "gia-toc", "gia_toc"],
        "start_linh_thach": 30,
        "hp": 110,
        "mp": 40,
        "atk": 10,
        "defense": 8,
        "train_bonus": 5,
        "break_bonus": 10,
    },
    "xuyenkhong": {
        "name": "Xuyên Không / Trùng Sinh",
        "lore": "Ký ức từ một đời khác thức tỉnh. Ngươi hiểu sớm hơn người thường rất nhiều về con đường tu tiên.",
        "aliases": ["xuyenkhong", "xuyen-khong", "trungsinh", "trung-sinh"],
        "start_linh_thach": 15,
        "hp": 100,
        "mp": 70,
        "atk": 8,
        "defense": 6,
        "train_bonus": 15,
        "break_bonus": 12,
    },
    "phamnhan": {
        "name": "Phàm Nhân Cầu Đạo",
        "lore": "Từ một người bình thường bước vào tiên môn, ngươi không có hậu thuẫn, chỉ có ý chí và một tia cơ duyên mỏng manh.",
        "aliases": ["phamnhan", "phamnhand", "phàmnhân", "phàm-nhân"],
        "start_linh_thach": 0,
        "hp": 100,
        "mp": 50,
        "atk": 5,
        "defense": 5,
        "train_bonus": 5,
        "break_bonus": 5,
    },
}

CONG_PHAP = {
    "kiem": {
        "name": "Kiếm Tu",
        "lore": "Nhất kiếm phá vạn pháp. Tốc độ ra đòn cao, sát khí mạnh.",
        "aliases": ["kiem", "kiemtu", "kiem-tu", "kiem_tu"],
        "hp": 0,
        "mp": 10,
        "atk": 20,
        "defense": 0,
        "train_bonus": 5,
        "break_bonus": 5,
    },
    "phap": {
        "name": "Pháp Tu",
        "lore": "Dùng trận pháp và linh pháp áp chế đối thủ, thiên về bùng nổ.",
        "aliases": ["phap", "phaptu", "phap-tu", "phap_tu"],
        "hp": 0,
        "mp": 25,
        "atk": 10,
        "defense": 5,
        "train_bonus": 8,
        "break_bonus": 3,
    },
    "the": {
        "name": "Thể Tu",
        "lore": "Thân thể là pháp bảo. Trâu bò, chống chịu cực tốt.",
        "aliases": ["the", "thetu", "the-tu", "the_tu"],
        "hp": 30,
        "mp": 0,
        "atk": 8,
        "defense": 20,
        "train_bonus": 5,
        "break_bonus": 8,
    },
}

ITEMS = {
    "hoi_xuan": {
        "name": "Cuộn Công Pháp Hồi Xuân",
        "type": "special",
        "description": "Dùng để hồi xuân, reset tuổi và tái sinh.",
    },
    "linh_dan": {
        "name": "Linh Đan",
        "type": "consumable",
        "description": "Tăng một lượng nhỏ tu vi.",
        "tu_vi_gain": (3, 8),
    },
    "phap_bao_co_ban": {
        "name": "Pháp Bảo Cổ",
        "type": "equipment",
        "description": "Tăng nhẹ công kích và phòng thủ.",
        "atk": (4, 10),
        "defense": (3, 8),
    },
    "cong_phap_tan_thu": {
        "name": "Công Pháp Tàn Quyển",
        "type": "consumable",
        "description": "Dùng để kích hoạt cơ duyên tu luyện cơ bản.",
    },
}

BICANH_TIERS = [
    {
        "key": "tieu",
        "name": "Thanh Vân Bí Cảnh",
        "train_mult": 1.15,
        "drop_mult": 1.10,
        "loot_mult": 1.05,
        "max_age": None,
    },
    {
        "key": "trung",
        "name": "Linh Vụ Bí Cảnh",
        "train_mult": 1.30,
        "drop_mult": 1.20,
        "loot_mult": 1.15,
        "max_age": 120,
    },
    {
        "key": "cao",
        "name": "Huyết Linh Bí Cảnh",
        "train_mult": 1.50,
        "drop_mult": 1.35,
        "loot_mult": 1.25,
        "max_age": 90,
    },
    {
        "key": "dien",
        "name": "Thái Hư Bí Cảnh",
        "train_mult": 1.80,
        "drop_mult": 1.60,
        "loot_mult": 1.40,
        "max_age": 70,
    },
    {
        "key": "thienco",
        "name": "Cửu U Bí Cảnh",
        "train_mult": 2.10,
        "drop_mult": 2.00,
        "loot_mult": 1.60,
        "max_age": 50,
    },
]

BASE_HP = 100
BASE_MP = 50
BASE_ATK = 5
BASE_DEFENSE = 5
AGE_DAYS_PER_YEAR = 12


def normalize_choice(text: str):
    return "".join(ch for ch in text.lower().strip() if ch.isalnum())


def random_linh_can():
    return random.choices(LINH_CAN, weights=[x["rate"] for x in LINH_CAN], k=1)[0]


def find_origin(key_or_alias: str):
    key = normalize_choice(key_or_alias)
    for origin_key, origin in ORIGINS.items():
        aliases = [normalize_choice(origin_key)] + [normalize_choice(a) for a in origin["aliases"]]
        if key in aliases:
            return origin_key, origin
    return None, None


def find_cong_phap(key_or_alias: str):
    key = normalize_choice(key_or_alias)
    for path_key, path in CONG_PHAP.items():
        aliases = [normalize_choice(path_key)] + [normalize_choice(a) for a in path["aliases"]]
        if key in aliases:
            return path_key, path
    return None, None


def find_item(key_or_alias: str):
    key = normalize_choice(key_or_alias)
    for item_key, item in ITEMS.items():
        if key == normalize_choice(item_key) or key == normalize_choice(item["name"]):
            return item_key, item
    return None, None


def apply_cong_phap(user: dict, path_key: str):
    path = CONG_PHAP[path_key]
    user["cong_phap_key"] = path_key
    user["cong_phap_name"] = path["name"]
    user["hp"] = int(user.get("hp", BASE_HP)) + path["hp"]
    user["mp"] = int(user.get("mp", BASE_MP)) + path["mp"]
    user["atk"] = int(user.get("atk", BASE_ATK)) + path["atk"]
    user["defense"] = int(user.get("defense", BASE_DEFENSE)) + path["defense"]
    user["train_bonus"] = int(user.get("train_bonus", 0)) + path["train_bonus"]
    user["break_bonus"] = int(user.get("break_bonus", 0)) + path["break_bonus"]


def get_realm_name(user: dict):
    major_index = int(user.get("major_index", -1))
    minor_stage = int(user.get("minor_stage", 0))
    if major_index < 0:
        return "Phàm Nhân"
    major_index = min(major_index, len(MAJOR_REALMS) - 1)
    minor_stage = max(0, min(minor_stage, len(MINOR_STAGES) - 1))
    return f"{MAJOR_REALMS[major_index]} {MINOR_STAGES[minor_stage]}"


def next_minor_cost(cost: int):
    return max(1, math.ceil(cost * 1.5))


def prev_minor_cost(cost: int):
    return max(1, math.ceil(cost / 1.5))


def get_break_rate(user: dict):
    base = BREAKTHROUGH_RATES.get(int(user.get("major_index", -1)), 5)
    bonus = int(user.get("break_bonus", 0))
    return max(5, min(95, base + bonus))


def birth_time_from_age(age_years: int, now_ts: Optional[int] = None) -> int:
    now_ts = int(now_ts or time.time())
    age_years = max(0, int(age_years))
    return now_ts - age_years * AGE_DAYS_PER_YEAR * 86400


def get_age(user: dict, now_ts: Optional[int] = None) -> int:
    now_ts = int(now_ts or time.time())
    birth_time = int(user.get("birth_time", now_ts))
    days = max(0, now_ts - birth_time) // 86400
    return int(days // AGE_DAYS_PER_YEAR)


def age_penalty(age_years: int) -> float:
    if age_years < 30:
        return 1.0
    if age_years < 60:
        return 0.92
    if age_years < 100:
        return 0.80
    if age_years < 150:
        return 0.70
    return 0.60


def roll_bi_canh_tier():
    weights = [35, 28, 20, 12, 5]
    return random.choices(BICANH_TIERS, weights=weights, k=1)[0]


def generate_bi_canh_event(now_ts: Optional[int] = None) -> dict:
    now_ts = int(now_ts or time.time())
    tier = roll_bi_canh_tier()
    duration = random.randint(15 * 60, 25 * 60)
    max_age = tier["max_age"] if tier["max_age"] is not None and random.random() < 0.7 else None
    event_id = f"bc_{now_ts}_{random.randint(1000, 9999)}"
    return {
        "id": event_id,
        "tier_key": tier["key"],
        "name": tier["name"],
        "train_mult": tier["train_mult"],
        "drop_mult": tier["drop_mult"],
        "loot_mult": tier["loot_mult"],
        "max_age": max_age,
        "spawn_at": now_ts,
        "ends_at": now_ts + duration,
        "duration": duration,
        "announced": False,
        "players": [],
    }


def get_bi_canh_bonus(event: Optional[dict]) -> float:
    if not event:
        return 1.0
    return float(event.get("train_mult", 1.0))


def can_join_bi_canh(user: dict, event: Optional[dict]) -> Tuple[bool, str]:
    if not event:
        return False, "bí cảnh chưa mở"
    age = get_age(user)
    max_age = event.get("max_age")
    if max_age is not None and age > int(max_age):
        return False, "tuổi quá cao nên không thể vào bí cảnh này"
    return True, ""


def roll_y_canh_piece(source: str = "tu_luyen") -> dict:
    piece_type = random.choice(["att", "def"])
    combat_bonus = round(random.uniform(0.02, 0.10), 3)
    cultivation_bonus = round(random.uniform(0.02, 0.10), 3)
    return {
        "id": f"yc_{int(time.time())}_{random.randint(1000, 9999)}",
        "type": piece_type,
        "combat_bonus": combat_bonus,
        "cultivation_bonus": cultivation_bonus,
        "source": source,
    }


def summarize_y_canh(pieces: List[dict]) -> Dict[str, Any]:
    attack_bonus = 0.0
    defense_bonus = 0.0
    cultivation_bonus = 0.0
    for piece in pieces:
        combat_bonus = float(piece.get("combat_bonus", 0))
        cultivation_bonus += float(piece.get("cultivation_bonus", 0))
        if piece.get("type") == "att":
            attack_bonus += combat_bonus
        else:
            defense_bonus += combat_bonus
    return {
        "count": len(pieces),
        "attack_bonus": round(attack_bonus, 3),
        "defense_bonus": round(defense_bonus, 3),
        "cultivation_bonus": round(cultivation_bonus, 3),
    }


def add_title(user: dict, title: str):
    titles = list(user.get("titles", []))
    if title not in titles:
        titles.append(title)
    user["titles"] = titles


def reset_user_for_rebirth(user: dict, keep_root: bool, now_ts: Optional[int] = None) -> dict:
    now_ts = int(now_ts or time.time())
    keep_root = bool(keep_root)
    current_root = None
    if keep_root:
        current_root = {
            "name": user.get("linh_can", "Ngũ Linh Căn"),
            "train_bonus": int(user.get("root_train_bonus", 0)),
            "break_bonus": int(user.get("root_break_bonus", 0)),
        }

    if not keep_root:
        current_root = random_linh_can()

    user["major_index"] = -1
    user["minor_stage"] = 0
    user["minor_cost"] = 10
    user["tu_vi"] = 0
    user["hp"] = BASE_HP
    user["mp"] = BASE_MP
    user["atk"] = BASE_ATK
    user["defense"] = BASE_DEFENSE
    user["cong_phap_key"] = ""
    user["cong_phap_name"] = "Chưa chọn"
    user["train_bonus"] = int(current_root.get("train_bonus", 0))
    user["break_bonus"] = int(current_root.get("break_bonus", 0))
    user["root_train_bonus"] = int(current_root.get("train_bonus", 0))
    user["root_break_bonus"] = int(current_root.get("break_bonus", 0))
    user["linh_can"] = current_root.get("name", user.get("linh_can", "Ngũ Linh Căn"))
    user["birth_time"] = birth_time_from_age(random.randint(12, 30), now_ts)
    user["y_canh_pieces"] = []
    user["in_bi_canh_id"] = ""
    user["current_bi_canh_id"] = ""
    user["rebirth_count"] = int(user.get("rebirth_count", 0)) + 1
    return user
