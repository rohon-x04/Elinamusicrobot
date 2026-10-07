# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Database layer (Firebase Realtime Database, REST)
# ============================================================
# Tree layout:
#   /welcome/<chat_id>       {message, enabled, card}
#   /music_favs/<user_id>/<video_id>   (see music/favs.py)
# ============================================================

import time
import logging
import httpx
from config import FIREBASE_URL, FIREBASE_SECRET

_client = httpx.AsyncClient(timeout=15)


def _url(path: str) -> str:
    url = f"{FIREBASE_URL}{path}.json"
    if FIREBASE_SECRET:
        url += f"?auth={FIREBASE_SECRET}"
    return url


async def _get(path: str):
    resp = await _client.get(_url(path))
    resp.raise_for_status()
    return resp.json()


async def _put(path: str, data):
    resp = await _client.put(_url(path), json=data)
    resp.raise_for_status()
    return resp.json()


async def _patch(path: str, data: dict):
    resp = await _client.patch(_url(path), json=data)
    resp.raise_for_status()
    return resp.json()


async def _delete(path: str):
    resp = await _client.delete(_url(path))
    resp.raise_for_status()


# Short-lived read cache (welcome settings are read on every join).
_cache: dict = {}
_CACHE_TTL = 20  # seconds


async def _cached_get(path: str, ttl: float = _CACHE_TTL):
    now = time.monotonic()
    hit = _cache.get(path)
    if hit and hit[0] > now:
        return hit[1]
    data = await _get(path)
    if len(_cache) > 5000:
        _cache.clear()
    _cache[path] = (now + ttl, data)
    return data


def _invalidate(prefix: str):
    for key in [k for k in _cache if k.startswith(prefix)]:
        _cache.pop(key, None)


# ==========================================================
# 🟢 Welcome
# ==========================================================

async def set_welcome_message(chat_id, text: str):
    await _patch(f"/welcome/{chat_id}", {"message": text})
    _invalidate(f"/welcome/{chat_id}")


async def reset_welcome_message(chat_id):
    await _delete(f"/welcome/{chat_id}/message")
    _invalidate(f"/welcome/{chat_id}")


async def get_welcome_message(chat_id):
    data = await _cached_get(f"/welcome/{chat_id}")
    return data.get("message") if data else None


async def set_welcome_status(chat_id, status: bool):
    await _patch(f"/welcome/{chat_id}", {"enabled": status})
    _invalidate(f"/welcome/{chat_id}")


async def get_welcome_status(chat_id) -> bool:
    data = await _cached_get(f"/welcome/{chat_id}")
    return bool(data.get("enabled", True)) if data else True


async def set_welcome_card(chat_id, enabled: bool):
    await _patch(f"/welcome/{chat_id}", {"card": enabled})
    _invalidate(f"/welcome/{chat_id}")


async def get_welcome_card(chat_id) -> bool:
    data = await _cached_get(f"/welcome/{chat_id}")
    return bool(data.get("card", True)) if data else True


# ==========================================================
# 📣 Broadcast targets  (/bc_chats/<chat_id>, /bc_users/<user_id>)
# ==========================================================

async def add_chat(chat_id):
    await _put(f"/bc_chats/{chat_id}", True)


async def remove_chat(chat_id):
    await _delete(f"/bc_chats/{chat_id}")


async def add_user(user_id):
    await _put(f"/bc_users/{user_id}", True)


async def remove_user(user_id):
    await _delete(f"/bc_users/{user_id}")


async def get_chats() -> list:
    data = await _get("/bc_chats")
    return [int(k) for k in data] if isinstance(data, dict) else []


async def get_users() -> list:
    data = await _get("/bc_users")
    return [int(k) for k in data] if isinstance(data, dict) else []


# ==========================================================
# 📣 Broadcast registry  (/users/<id> = true, /chats/<id> = true)
# ==========================================================

_known_users: set = set()
_known_chats: set = set()


async def _get_keys(path: str) -> list:
    """Return only the child keys of a node (cheap - no values downloaded)."""
    url = _url(path)
    url += ("&" if "?" in url else "?") + "shallow=true"
    resp = await _client.get(url, timeout=60)
    resp.raise_for_status()
    data = resp.json() or {}
    return list(data.keys())


async def add_user(user_id: int):
    if user_id in _known_users:
        return
    _known_users.add(user_id)
    try:
        await _put(f"/users/{user_id}", True)
    except Exception as e:
        _known_users.discard(user_id)
        logging.warning(f"add_user failed: {e}")


async def add_chat(chat_id: int):
    if chat_id in _known_chats:
        return
    _known_chats.add(chat_id)
    try:
        await _put(f"/chats/{chat_id}", True)
    except Exception as e:
        _known_chats.discard(chat_id)
        logging.warning(f"add_chat failed: {e}")


async def remove_user(user_id: int):
    _known_users.discard(user_id)
    try:
        await _delete(f"/users/{user_id}")
    except Exception:
        pass


async def remove_chat(chat_id: int):
    _known_chats.discard(chat_id)
    try:
        await _delete(f"/chats/{chat_id}")
    except Exception:
        pass


async def get_all_users() -> list:
    return [int(k) for k in await _get_keys("/users")]


async def get_all_chats() -> list:
    return [int(k) for k in await _get_keys("/chats")]


# ==========================================================
# 🎧 Assistant session string (set with /setstring in the bot's DM)
# ==========================================================

async def set_string_session(session: str):
    await _put("/settings/string_session", session)


async def get_string_session() -> str:
    data = await _get("/settings/string_session")
    return data if isinstance(data, str) else ""


async def delete_string_session():
    await _delete("/settings/string_session")
