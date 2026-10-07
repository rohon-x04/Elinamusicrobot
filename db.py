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
