# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: song cache in Firebase Realtime Database
# ============================================================
# A song is downloaded from the music API ONCE. The file is cut into chunks, saved to
# Firebase and from then on every play (any group, any restart, any server) is served
# from Firebase instead of the API.
#
#   /music_cache/<video_id>/<n>      base64 chunk n of the mp3
#   /music_cache_meta/<video_id>     {n, size, ts, title}   <- written LAST = "upload complete"
#
# A half-uploaded song has no meta node, so it is never played. Old songs are removed
# (least recently played first) when the total goes over MUSIC_CACHE_MAX_MB.

import asyncio
import base64
import logging
import os
import time

from config import FIREBASE_URL
from .settings import MUSIC_CACHE, MUSIC_CACHE_MAX_MB, MUSIC_CACHE_MAX_SONG_MB

log = logging.getLogger("music")

CHUNK = 384 * 1024            # raw bytes per Firebase node (~512 KB after base64)
enabled = bool(MUSIC_CACHE and FIREBASE_URL)

_index = None                 # vid -> {"n","size","ts","title"}   (None = not loaded yet)
_load_lock = asyncio.Lock()
_uploading: set = set()
_TOUCH_EVERY = 3600           # refresh "last played" at most once an hour per song


async def _load() -> dict:
    global _index
    if _index is not None:
        return _index
    async with _load_lock:
        if _index is None:
            import db
            try:
                data = await db._get("/music_cache_meta")
                _index = {k: v for k, v in (data or {}).items() if isinstance(v, dict)}
                log.info("💾 song cache: %d songs, %.0f MB", len(_index), _total(_index) / 2**20)
            except Exception as e:
                log.warning("💾 song cache unavailable right now: %s", e)
                return {}
    return _index


def _total(idx: dict) -> int:
    return sum(int(m.get("size", 0)) for m in idx.values())


async def has(vid: str) -> bool:
    return enabled and bool(vid) and vid in await _load()


async def fetch(vid: str, path: str) -> bool:
    """Rebuild the song file at `path` from Firebase. False = not cached / failed."""
    if not enabled or not vid:
        return False
    meta = (await _load()).get(vid)
    if not meta:
        return False
    import db
    n, size = int(meta["n"]), int(meta["size"])
    sem = asyncio.Semaphore(6)

    async def one(i: int) -> bytes:
        async with sem:
            s = await db._get(f"/music_cache/{vid}/{i}")
            if not isinstance(s, str):
                raise LookupError(f"chunk {i} missing")
            return base64.b64decode(s)

    part = path + ".part"
    try:
        data = b"".join(await asyncio.gather(*[one(i) for i in range(n)]))
        if len(data) != size:
            raise LookupError("size mismatch")
        await asyncio.to_thread(_write, part, data)
        os.replace(part, path)
    except LookupError as e:                       # damaged entry: forget it, it will be saved again
        log.warning("💾 cache entry %s is damaged (%s) - removing", vid, e)
        await _drop(vid)
        _rm(part)
        return False
    except Exception as e:                         # network problem: keep the entry, just fall back
        log.warning("💾 cache read failed for %s: %s", vid, e)
        _rm(part)
        return False
    _touch(vid, meta)
    log.info("💾 cache hit %s (%.1f MB)", vid, size / 2**20)
    return True


def _write(p: str, data: bytes):
    with open(p, "wb") as f:
        f.write(data)


def _rm(p: str):
    try:
        os.remove(p)
    except OSError:
        pass


def _touch(vid: str, meta: dict):
    now = int(time.time())
    if now - int(meta.get("ts", 0)) < _TOUCH_EVERY:
        return
    meta["ts"] = now

    async def _go():
        try:
            import db
            await db._patch(f"/music_cache_meta/{vid}", {"ts": now})
        except Exception:
            pass
    asyncio.create_task(_go())


async def store(vid: str, path: str, title: str = ""):
    """Save a downloaded song to Firebase (safe to call many times - it only uploads once)."""
    if not enabled or not vid or vid in _uploading:
        return
    idx = await _load()
    if vid in idx or _index is None:
        return
    _uploading.add(vid)
    try:
        try:
            data = await asyncio.to_thread(lambda: open(path, "rb").read())
        except OSError:
            return
        if not data or len(data) > MUSIC_CACHE_MAX_SONG_MB * 2**20:
            return
        import db
        pieces = [data[i:i + CHUNK] for i in range(0, len(data), CHUNK)]
        sem = asyncio.Semaphore(4)

        async def up(i: int, b: bytes):
            async with sem:
                await db._put(f"/music_cache/{vid}/{i}", base64.b64encode(b).decode())

        try:
            await asyncio.gather(*[up(i, b) for i, b in enumerate(pieces)])
            meta = {"n": len(pieces), "size": len(data), "ts": int(time.time()), "title": title[:80]}
            await db._put(f"/music_cache_meta/{vid}", meta)       # commit marker, written last
        except Exception as e:
            log.warning("💾 could not save %s to the cache: %s", vid, e)
            try:
                await db._delete(f"/music_cache/{vid}")
            except Exception:
                pass
            return
        idx[vid] = meta
        log.info("💾 saved %s to the cache (%.1f MB)", vid, len(data) / 2**20)
        await _evict(keep=vid)
    finally:
        _uploading.discard(vid)


def store_bg(vid: str, path: str, title: str = ""):
    t = asyncio.create_task(store(vid, path, title))
    t.add_done_callback(lambda f: f.exception() and log.warning("cache store failed: %s", f.exception()))


async def _drop(vid: str):
    import db
    (_index or {}).pop(vid, None)
    for node in (f"/music_cache_meta/{vid}", f"/music_cache/{vid}"):   # meta first: never half-visible
        try:
            await db._delete(node)
        except Exception:
            pass


async def _evict(keep: str = ""):
    idx = _index or {}
    limit = MUSIC_CACHE_MAX_MB * 2**20
    while idx and _total(idx) > limit:
        victims = [k for k in idx if k != keep]
        if not victims:
            break
        old = min(victims, key=lambda k: int(idx[k].get("ts", 0)))
        log.info("💾 cache full - removing the least recently played song %s", old)
        await _drop(old)


async def stats() -> tuple:
    """(songs, megabytes)"""
    idx = await _load()
    return len(idx), _total(idx) / 2**20


async def clear() -> int:
    import db
    idx = await _load()
    n = len(idx)
    for node in ("/music_cache_meta", "/music_cache"):
        await db._delete(node)
    idx.clear()
    return n
