import math
import os
import random
import time
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from logic import (
    CONG_PHAP,
    MAJOR_REALMS,
    MINOR_STAGES,
    ORIGINS,
    apply_cong_phap,
    find_cong_phap,
    find_origin,
    get_break_rate,
    get_realm_name,
    next_minor_cost,
    prev_minor_cost,
)
from store import create_user, get_user, load_db, save_db, update_user

app = FastAPI(title="ThienDao Backend")


class StartIn(BaseModel):
    user_id: int
    name: str
    origin_input: Optional[str] = None


class ChoosePathIn(BaseModel):
    user_id: int
    choice: str


class UserOnlyIn(BaseModel):
    user_id: int


def user_or_404(user_id: int) -> Dict[str, Any]:
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user


@app.on_event("startup")
def on_startup():
    load_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/user/start")
def start(payload: StartIn):
    existing = get_user(payload.user_id)
    if existing:
        existing["id"] = payload.user_id
        return {
            "ok": False,
            "error": "already_registered",
            "user": existing,
            "realm_text": get_realm_name(existing),
        }

    chosen_key, chosen_origin = None, None
    if payload.origin_input:
        chosen_key, chosen_origin = find_origin(payload.origin_input)
    if not chosen_origin:
        chosen_key = random.choice(list(ORIGINS.keys()))
        chosen_origin = ORIGINS[chosen_key]

    user = create_user(payload.user_id, payload.name, chosen_key)
    user["id"] = payload.user_id
    save_db()
    return {"ok": True, "user": user, "origin": chosen_origin}


@app.get("/user/profile")
def profile(user_id: int):
    user = user_or_404(user_id)
    user["id"] = user_id
    return {"ok": True, "user": user, "realm_text": get_realm_name(user)}


@app.post("/user/congphap")
def congphap(payload: ChoosePathIn):
    user = user_or_404(payload.user_id)
    if user.get("cong_phap_key"):
        return {"ok": False, "error": "already_chosen", "user": user}

    path_key, path = find_cong_phap(payload.choice)
    if not path:
        return {"ok": False, "error": "invalid_choice"}

    apply_cong_phap(user, path_key)
    update_user(payload.user_id, user)
    save_db()
    return {"ok": True, "user": user, "path": path}


@app.post("/user/daily")
def daily(payload: UserOnlyIn):
    user = user_or_404(payload.user_id)
    now = int(time.time())
    cooldown = int(user.get("daily_cooldown", 60))
    last_daily = int(user.get("last_daily", 0))
    if now - last_daily < cooldown:
        return {"ok": False, "error": "cooldown", "remain": cooldown - (now - last_daily)}

    reward = random.randint(50, 200)
    reward = int(reward + user.get("train_bonus", 0) * 0.5)
    user["linh_thach"] = int(user.get("linh_thach", 0) + reward)
    user["last_daily"] = now
    update_user(payload.user_id, user)
    save_db()
    return {"ok": True, "reward": reward, "user": user}


@app.post("/user/train")
def train(payload: UserOnlyIn):
    user = user_or_404(payload.user_id)

    if int(user.get("major_index", -1)) == -1:
        cost = 10
        if user.get("linh_thach", 0) < cost:
            return {"ok": False, "error": "not_enough_linh_thach", "need": cost}
        user["linh_thach"] -= cost
        user["major_index"] = 0
        user["minor_stage"] = 0
        user["minor_cost"] = 10
        user["tu_vi"] = int(user.get("tu_vi", 0)) + 1
        update_user(payload.user_id, user)
        save_db()
        return {"ok": True, "kind": "init", "user": user, "realm_text": get_realm_name(user)}

    if int(user.get("minor_stage", 0)) == 3:
        return {"ok": False, "error": "need_breakthrough", "realm_text": get_realm_name(user)}

    cost = int(user.get("minor_cost", 10))
    if user.get("linh_thach", 0) < cost:
        return {"ok": False, "error": "not_enough_linh_thach", "need": cost}

    user["linh_thach"] -= cost
    user["minor_stage"] = int(user.get("minor_stage", 0)) + 1
    user["tu_vi"] = int(user.get("tu_vi", 0)) + 1

    if user["minor_stage"] < 3:
        user["minor_cost"] = next_minor_cost(cost)

    update_user(payload.user_id, user)
    save_db()
    return {
        "ok": True,
        "kind": "train",
        "user": user,
        "realm_text": get_realm_name(user),
        "next_cost": user["minor_cost"],
        "cost": cost,
    }


@app.post("/user/breakthrough")
def breakthrough(payload: UserOnlyIn):
    user = user_or_404(payload.user_id)

    if int(user.get("major_index", -1)) == -1:
        return {"ok": False, "error": "not_started"}
    if int(user.get("minor_stage", 0)) < 3:
        return {"ok": False, "error": "not_ready", "realm_text": get_realm_name(user)}
    if int(user.get("major_index", -1)) >= len(MAJOR_REALMS) - 1:
        return {"ok": False, "error": "max_realm"}

    break_cost = math.ceil(int(user.get("minor_cost", 10)) * 2)
    if user.get("linh_thach", 0) < break_cost:
        return {"ok": False, "error": "not_enough_linh_thach", "need": break_cost}

    rate = get_break_rate(user)
    roll = random.randint(1, 100)
    user["linh_thach"] -= break_cost

    if roll <= rate:
        user["major_index"] += 1
        user["minor_stage"] = 0
        user["minor_cost"] = 10
        user["tu_vi"] = int(user.get("tu_vi", 0)) + 1
        update_user(payload.user_id, user)
        save_db()
        return {
            "ok": True,
            "success": True,
            "rate": rate,
            "roll": roll,
            "break_cost": break_cost,
            "user": user,
            "realm_text": get_realm_name(user),
        }

    backlash_hp = random.randint(5, 15)
    user["hp"] = max(1, int(user.get("hp", 100)) - backlash_hp)

    dropped = False
    if int(user.get("minor_stage", 0)) > 0 and random.random() < 0.5:
        user["minor_stage"] = int(user["minor_stage"]) - 1
        user["minor_cost"] = prev_minor_cost(int(user.get("minor_cost", 10)))
        dropped = True

    extra_loss = max(1, math.ceil(break_cost * 0.15))
    user["linh_thach"] = max(0, int(user.get("linh_thach", 0)) - extra_loss)

    update_user(payload.user_id, user)
    save_db()
    return {
        "ok": True,
        "success": False,
        "rate": rate,
        "roll": roll,
        "break_cost": break_cost,
        "realm_text": get_realm_name(user),
        "backlash_hp": backlash_hp,
        "extra_loss": extra_loss,
        "dropped": dropped,
        "user": user,
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
