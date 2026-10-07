# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: favourites (saved per user)
# ============================================================
# Stored in the Firebase database under /music_favs/<user_id>/<video_id>.
# If Firebase isn't reachable the favourites live in memory only.

import logging

log = logging.getLogger("music")
_mem: dict[int, dict] = {}


async def _fb_get(user_id: int):
    import db
    return await db._get(f"/music_favs/{user_id}")


async def get_favs(user_id: int) -> list[tuple[str, str, int]]:
    """[(video_id, title, duration_seconds), ...] oldest first."""
    try:
        data = await _fb_get(user_id) or {}
    except Exception as e:
        log.warning(f"favs read failed: {e}")
        data = _mem.get(user_id, {})
    items = sorted(data.items(), key=lambda kv: kv[1].get("at", 0))
    return [(vid, v.get("title", "?"), int(v.get("dur", 0))) for vid, v in items]


async def add_fav(user_id: int, track) -> bool:
    """Save the track. Returns False if it was already a favourite."""
    import time
    if not track.vid:
        return False
    if any(v == track.vid for v, _, _ in await get_favs(user_id)):
        return False
    entry = {"title": track.title[:100], "dur": track.duration, "at": int(time.time())}
    _mem.setdefault(user_id, {})[track.vid] = entry
    try:
        import db
        await db._put(f"/music_favs/{user_id}/{track.vid}", entry)
    except Exception as e:
        log.warning(f"favs write failed: {e}")
    return True
