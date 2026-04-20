import math
import random

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


def apply_cong_phap(user: dict, path_key: str):
    path = CONG_PHAP[path_key]
    user["cong_phap_key"] = path_key
    user["cong_phap_name"] = path["name"]
    user["hp"] += path["hp"]
    user["mp"] += path["mp"]
    user["atk"] += path["atk"]
    user["defense"] += path["defense"]
    user["train_bonus"] += path["train_bonus"]
    user["break_bonus"] += path["break_bonus"]


def get_realm_name(user: dict):
    if user["major_index"] == -1:
        return "Phàm Nhân"
    return f"{MAJOR_REALMS[user['major_index']]} {MINOR_STAGES[user['minor_stage']]}"


def next_minor_cost(cost: int):
    return max(1, math.ceil(cost * 1.5))


def prev_minor_cost(cost: int):
    return max(1, math.ceil(cost / 1.5))


def get_break_rate(user: dict):
    base = BREAKTHROUGH_RATES.get(user["major_index"], 5)
    bonus = user.get("break_bonus", 0)
    return max(5, min(95, base + bonus))
