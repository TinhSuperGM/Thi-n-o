import asyncio
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
    ITEMS,
    MAJOR_REALMS,
    MINOR_STAGES,
    ORIGINS,
    add_title,
    age_penalty,
    apply_cong_phap,
    can_join_bi_canh,
    find_cong_phap,
    find_item,
    find_origin,
    generate_bi_canh_event,
    get_age,
    get_bi_canh_bonus,
    get_break_rate,
    get_realm_name,
    next_minor_cost,
    prev_minor_cost,
    normalize_choice,
    reset_user_for_rebirth,
    roll_y_canh_piece,
    summarize_y_canh,
)
from store import (
    clear_current_bi_canh,
    clear_users_from_bi_canh,
    create_user,
    get_current_bi_canh,
    get_guild_bicanh_channels,
    get_user,
    load_db,
    save_db,
    set_current_bi_canh,
    set_guild_bicanh_channel,
    set_user_in_bi_canh,
    update_user,
)

app = FastAPI(title="ThienDao Backend")
_scheduler_started = False


class StartIn(BaseModel):
    user_id: int
    name: str
    origin_input: Optional[str] = None


class ChoosePathIn(BaseModel):
    user_id: int
    choice: str


class UserOnlyIn(BaseModel):
    user_id: int


class UseItemIn(BaseModel):
    user_id: int
    item: str
    keep_root: Optional[bool] = False


class GuildBicanhIn(BaseModel):
    guild_id: int
    channel_id: int


class BicanhJoinIn(BaseModel):
    user_id: int


class BicanhActionIn(BaseModel):
    user_id: int


def user_or_404(user_id: int) -> Dict[str, Any]:
    user = get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user_not_found")
    return user


async def bi_canh_scheduler() -> None:
    while True:
        current = get_current_bi_canh()
        now = int(time.time())

        if current:
            ends_at = int(current.get("ends_at", 0))
            if ends_at <= now:
                clear_users_from_bi_canh(current.get("id", ""))
                clear_current_bi_canh()
                save_db()
                await asyncio.sleep(10)
                continue
            await asyncio.sleep(20)
            continue

        await asyncio.sleep(random.randint(30 * 60, 90 * 60))
        if get_current_bi_canh():
            continue

        event = generate_bi_canh_event()
        set_current_bi_canh(event)
        save_db()


@app.on_event("startup")
async def on_startup():
    global _scheduler_started
    load_db()
    if not _scheduler_started:
        asyncio.create_task(bi_canh_scheduler())
        _scheduler_started = True


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/guild/bicanh-channels")
def guild_bicanh_channels():
    return {"ok": True, "channels": get_guild_bicanh_channels()}


@app.post("/guild/setup/bicanh-channel")
def setup_bicanh_channel(payload: GuildBicanhIn):
    cfg = set_guild_bicanh_channel(payload.guild_id, payload.channel_id)
    save_db()
    return {"ok": True, "config": cfg}


@app.get("/bicanh/current")
def current_bicanh():
    event = get_current_bi_canh()
    if not event:
        return {"ok": True, "active": False, "event": None}
    event = dict(event)
    remaining = max(0, int(event.get("ends_at", 0)) - int(time.time()))
    event["remaining"] = remaining
    return {"ok": True, "active": True, "event": event}


@app.post("/bicanh/mark-announced")
def mark_bicanh_announced():
    event = get_current_bi_canh()
    if not event:
        return {"ok": False, "error": "no_active_event"}
    event["announced"] = True
    set_current_bi_canh(event)
    save_db()
    return {"ok": True, "event": event}


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
    age = get_age(user)
    y_info = summarize_y_canh(list(user.get("y_canh_pieces", [])))
    current_event = get_current_bi_canh()
    if current_event and user.get("in_bi_canh_id") == current_event.get("id"):
        current_event = dict(current_event)
        current_event["remaining"] = max(0, int(current_event.get("ends_at", 0)) - int(time.time()))
    else:
        current_event = None
    return {
        "ok": True,
        "user": user,
        "realm_text": get_realm_name(user),
        "age": age,
        "y_canh": y_info,
        "current_bi_canh": current_event,
    }


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


@app.post("/user/use")
def use_item(payload: UseItemIn):
    user = user_or_404(payload.user_id)
    choice = normalize_choice(payload.item)
    path_key, path = find_cong_phap(choice)
    if path:
        if user.get("cong_phap_key"):
            return {"ok": False, "error": "already_chosen", "user": user}
        apply_cong_phap(user, path_key)
        update_user(payload.user_id, user)
        save_db()
        return {"ok": True, "kind": "congphap", "user": user, "path": path}

    item_key, item = find_item(choice)
    if not item:
        return {"ok": False, "error": "invalid_item"}

    bag = dict(user.get("bag_items", {}))
    if int(bag.get(item_key, 0)) <= 0:
        return {"ok": False, "error": "not_in_bag", "item": item}

    bag[item_key] = int(bag.get(item_key, 0)) - 1
    if bag[item_key] <= 0:
        bag.pop(item_key, None)
    user["bag_items"] = bag

    if item_key == "hoi_xuan":
        keep_root = bool(payload.keep_root)
        user = reset_user_for_rebirth(user, keep_root=keep_root)
        add_title(user, f"Luân Hồi Giả {user['rebirth_count']}")
        update_user(payload.user_id, user)
        save_db()
        return {
            "ok": True,
            "kind": "rebirth",
            "keep_root": keep_root,
            "user": user,
        }

    if item_key == "linh_dan":
        gain = random.randint(*item["tu_vi_gain"])
        user["tu_vi"] = int(user.get("tu_vi", 0)) + gain
        update_user(payload.user_id, user)
        save_db()
        return {"ok": True, "kind": "item", "effect": "tu_vi", "gain": gain, "user": user, "item": item}

    if item_key == "phap_bao_co_ban":
        atk = random.randint(*item["atk"])
        defense = random.randint(*item["defense"])
        user["atk"] = int(user.get("atk", 0)) + atk
        user["defense"] = int(user.get("defense", 0)) + defense
        update_user(payload.user_id, user)
        save_db()
        return {
            "ok": True,
            "kind": "item",
            "effect": "stat",
            "atk": atk,
            "defense": defense,
            "user": user,
            "item": item,
        }

    if item_key == "cong_phap_tan_thu":
        if user.get("cong_phap_key"):
            update_user(payload.user_id, user)
            save_db()
            return {"ok": True, "kind": "item", "effect": "none", "user": user, "item": item}
        path_key, path = random.choice(list(CONG_PHAP.items()))
        apply_cong_phap(user, path_key)
        update_user(payload.user_id, user)
        save_db()
        return {"ok": True, "kind": "congphap", "path": path, "user": user, "item": item}

    update_user(payload.user_id, user)
    save_db()
    return {"ok": True, "kind": "item", "user": user, "item": item}


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
    age = get_age(user)
    age_mult = age_penalty(age)
    current_event = get_current_bi_canh()
    in_bi_canh = bool(current_event and user.get("in_bi_canh_id") == current_event.get("id"))
    bicanh_mult = get_bi_canh_bonus(current_event) if in_bi_canh else 1.0

    if int(user.get("major_index", -1)) == -1:
        cost = 10
        if user.get("linh_thach", 0) < cost:
            return {"ok": False, "error": "not_enough_linh_thach", "need": cost}
        user["linh_thach"] -= cost
        user["major_index"] = 0
        user["minor_stage"] = 0
        user["minor_cost"] = 10
        gain = max(1, int(round((1 + int(user.get("train_bonus", 0)) / 100.0) * age_mult * bicanh_mult)))
        if random.random() < 0.08:
            gain += 1
        user["tu_vi"] = int(user.get("tu_vi", 0)) + gain
        fragment = None
        if int(user.get("major_index", 0)) < 4 and random.random() < min(0.10, 0.03 * bicanh_mult):
            fragment = roll_y_canh_piece(source="tu_luyen")
            pieces = list(user.get("y_canh_pieces", []))
            pieces.append(fragment)
            user["y_canh_pieces"] = pieces
        update_user(payload.user_id, user)
        save_db()
        return {"ok": True, "kind": "init", "gain": gain, "fragment": fragment, "user": user, "realm_text": get_realm_name(user)}

    cost = int(user.get("minor_cost", 10))
    if user.get("linh_thach", 0) < cost:
        return {"ok": False, "error": "not_enough_linh_thach", "need": cost}

    user["linh_thach"] -= cost

    if int(user.get("minor_stage", 0)) < 3:
        user["minor_stage"] = int(user.get("minor_stage", 0)) + 1
        if user["minor_stage"] < 3:
            user["minor_cost"] = next_minor_cost(cost)
    else:
        user["minor_stage"] = 3

    gain = max(1, int(round((1 + int(user.get("train_bonus", 0)) / 100.0) * age_mult * bicanh_mult)))
    if random.random() < 0.08:
        gain += 1
    user["tu_vi"] = int(user.get("tu_vi", 0)) + gain

    fragment = None
    if int(user.get("major_index", 0)) < 4 and random.random() < min(0.10, 0.03 * bicanh_mult):
        fragment = roll_y_canh_piece(source="tu_luyen")
        pieces = list(user.get("y_canh_pieces", []))
        pieces.append(fragment)
        user["y_canh_pieces"] = pieces

    update_user(payload.user_id, user)
    save_db()
    return {
        "ok": True,
        "kind": "train",
        "user": user,
        "realm_text": get_realm_name(user),
        "next_cost": user["minor_cost"],
        "cost": cost,
        "gain": gain,
        "fragment": fragment,
        "age": age,
        "age_mult": age_mult,
        "bi_canh_mult": bicanh_mult,
        "in_bi_canh": in_bi_canh,
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

    major_index = int(user.get("major_index", -1))
    minor_stage = int(user.get("minor_stage", 0))

    if major_index == 3 and minor_stage == 3:
        pieces = list(user.get("y_canh_pieces", []))
        if len(pieces) < 4:
            return {
                "ok": False,
                "error": "need_y_canh",
                "need": 4,
                "have": len(pieces),
                "realm_text": get_realm_name(user),
            }

    rate = get_break_rate(user)
    roll = random.randint(1, 100)
    user["linh_thach"] -= break_cost

    if roll <= rate:
        user["major_index"] += 1
        user["minor_stage"] = 0
        user["minor_cost"] = 10
        user["tu_vi"] = int(user.get("tu_vi", 0)) + 1
        if major_index == 3 and minor_stage == 3:
            pieces = list(user.get("y_canh_pieces", []))
            user["y_canh_pieces"] = pieces[4:]
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
        user["minor_stage"] = int(user.get("minor_stage")) - 1
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


@app.post("/bicanh/join")
def join_bicanh(payload: BicanhJoinIn):
    user = user_or_404(payload.user_id)
    event = get_current_bi_canh()
    if not event:
        return {"ok": False, "error": "no_active_event"}

    allowed, reason = can_join_bi_canh(user, event)
    if not allowed:
        return {"ok": False, "error": "age_blocked", "reason": reason, "event": event, "age": get_age(user)}

    players = list(event.get("players", []))
    if payload.user_id not in players:
        players.append(payload.user_id)
    event["players"] = players
    set_current_bi_canh(event)
    set_user_in_bi_canh(payload.user_id, event["id"])
    save_db()
    return {"ok": True, "event": event, "age": get_age(user)}


@app.post("/bicanh/leave")
def leave_bicanh(payload: BicanhActionIn):
    user = user_or_404(payload.user_id)
    event = get_current_bi_canh()
    if not event:
        user["in_bi_canh_id"] = ""
        user["current_bi_canh_id"] = ""
        update_user(payload.user_id, user)
        save_db()
        return {"ok": True, "event": None}

    players = list(event.get("players", []))
    if payload.user_id in players:
        players.remove(payload.user_id)
    event["players"] = players
    set_current_bi_canh(event)
    user["in_bi_canh_id"] = ""
    user["current_bi_canh_id"] = ""
    update_user(payload.user_id, user)
    save_db()
    return {"ok": True, "event": event}


@app.post("/bicanh/expedition")
def bi_canh_expedition(payload: BicanhActionIn):
    user = user_or_404(payload.user_id)
    event = get_current_bi_canh()
    if not event:
        return {"ok": False, "error": "no_active_event"}
    if user.get("in_bi_canh_id") != event.get("id"):
        return {"ok": False, "error": "not_joined"}

    age = get_age(user)
    age_mult = age_penalty(age)
    reward_mult = float(event.get("loot_mult", 1.0))
    train_mult = float(event.get("train_mult", 1.0))

    linh_thach_gain = random.randint(80, 250)
    linh_thach_gain = int(linh_thach_gain * reward_mult * age_mult)
    user["linh_thach"] = int(user.get("linh_thach", 0)) + linh_thach_gain

    gain = max(1, int(round((1 + int(user.get("train_bonus", 0)) / 100.0) * age_mult * train_mult)))
    user["tu_vi"] = int(user.get("tu_vi", 0)) + gain

    items = []
    if random.random() < min(0.35, 0.10 * reward_mult):
        item_key = random.choice(["linh_dan", "phap_bao_co_ban", "cong_phap_tan_thu"])
        bag = dict(user.get("bag_items", {}))
        bag[item_key] = int(bag.get(item_key, 0)) + 1
        user["bag_items"] = bag
        items.append(item_key)

    fragment = None
    if int(user.get("major_index", 0)) < 4 and random.random() < min(0.20, 0.05 * float(event.get("drop_mult", 1.0))):
        fragment = roll_y_canh_piece(source="bicanh")
        pieces = list(user.get("y_canh_pieces", []))
        pieces.append(fragment)
        user["y_canh_pieces"] = pieces

    update_user(payload.user_id, user)
    save_db()
    return {
        "ok": True,
        "event": event,
        "gain": gain,
        "linh_thach_gain": linh_thach_gain,
        "items": items,
        "fragment": fragment,
        "user": user,
        "realm_text": get_realm_name(user),
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
