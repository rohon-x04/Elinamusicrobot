# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: song lookup + third-party API download
# ============================================================
# * Titles / durations / thumbnails come from py-yt-search (as in your Youtube.py).
# * The AUDIO/VIDEO FILE comes ONLY from the third-party API (MUSIC_API_KEY).
#   There is no yt-dlp and no other fallback.

import os
import re
import asyncio
import logging
import random
import time
from dataclasses import dataclass

import httpx

from . import cache
from .settings import (MUSIC_API_URL, MUSIC_API_KEY, MUSIC_API_TIMEOUT,
                       MUSIC_API_QUALITY, MUSIC_API_VIDEO_QUALITY, MUSIC_DIRECT_STREAM)

log = logging.getLogger("music")

API_ENABLED = bool(MUSIC_API_URL and MUSIC_API_KEY)
DOWNLOAD_DIR = "downloads"


class StreamError(RuntimeError):
    """Could not get playable media for a track (message is user-facing)."""


@dataclass
class Track:
    title: str
    url: str                 # public page URL (shown to users)
    duration: int            # seconds
    thumb: str
    video: bool
    requested_by: str
    vid: str = ""            # YouTube video id
    channel: str = ""        # uploader / artist channel
    file_path: str = ""      # downloaded file
    requested_by_id: int = 0 # Telegram id of the requester (for the clickable name)
    thumb_task: object = None  # background task drawing the now-playing card
    stream_url: str = ""     # ready-to-play URL (live radio) - skips the API completely
    live: bool = False       # live radio station (no duration, can't seek)
    force_dl: bool = False   # direct streaming failed once -> download the file instead


def _dur_secs(d) -> int:
    if not d:
        return 0
    try:
        return sum(int(x) * 60 ** i for i, x in enumerate(reversed(str(d).split(":"))))
    except ValueError:
        return 0


def _to_track(r: dict, video: bool, user: str) -> Track:
    thumbs = r.get("thumbnails") or [{}]
    return Track(
        title=r.get("title") or "Unknown title",
        url=r.get("link") or f"https://www.youtube.com/watch?v={r['id']}",
        duration=_dur_secs(r.get("duration")),
        thumb=(thumbs[0].get("url") or "").split("?")[0],
        video=video,
        requested_by=user,
        vid=r["id"],
        channel=((r.get("channel") or {}).get("name") or ""),
    )


_search_cache: dict = {}
_search_inflight: dict = {}
SEARCH_TTL = 1800          # remember a search for 30 minutes
SEARCH_TIMEOUT = 8         # per attempt - a slow search is retried once instead of hanging
_YT_ID = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})")


async def _yt_search(query: str, limit: int) -> list:
    from py_yt import VideosSearch
    last = None
    for _ in range(2):                                   # one quick retry on a slow/failed search
        try:
            res = await asyncio.wait_for(VideosSearch(query, limit=limit).next(), SEARCH_TIMEOUT)
            return res.get("result") or []
        except Exception as e:                           # noqa: BLE001
            last = e
    raise last


async def _search_items(query: str) -> list:
    """Top results for a query. Cached, and identical searches that are running at the
    same moment share ONE request."""
    key = " ".join(query.lower().split())
    hit = _search_cache.get(key)
    if hit and hit[0] > time.monotonic():
        return hit[1]
    task = _search_inflight.get(key)
    if task is None:
        task = asyncio.create_task(_yt_search(query, 5))
        _search_inflight[key] = task
        task.add_done_callback(lambda _t, k=key: _search_inflight.pop(k, None))
    items = await asyncio.shield(task)
    if items:
        if len(_search_cache) > 300:
            _search_cache.clear()
        _search_cache[key] = (time.monotonic() + SEARCH_TTL, items)
    return items


async def search_track(query: str, video: bool, user: str) -> Track:
    """Find one song (by name or YouTube link). Raises LookupError if none.
    Repeated searches are answered from a small cache (instant)."""
    items = await _search_items(query)
    if not items:
        raise LookupError("nothing found")
    m = _YT_ID.search(query)
    pick = None
    if m:                                               # a link: take the exact video
        pick = next((r for r in items if r.get("id") == m.group(1)), None)
    if pick is None:                                    # a name: first real (non-live) result
        pick = next((r for r in items if r.get("id") and _dur_secs(r.get("duration"))), items[0])
    return _to_track(pick, video, user)


def warm(query: str) -> None:
    """Start a search in the background so the answer is cached when it is needed."""
    async def _go():
        try:
            await _search_items(query)
        except Exception:
            pass
    t = asyncio.create_task(_go())
    _bg.add(t)
    t.add_done_callback(_bg.discard)


# ---------------------------------------------------------------- API download
def _scrub(text: str) -> str:
    if MUSIC_API_KEY:
        text = text.replace(MUSIC_API_KEY, "***")
    return text


_http = None


def _client():
    """One shared client: connections stay open, so every download after the first
    skips the DNS + TLS handshake."""
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(MUSIC_API_TIMEOUT, connect=20),
            limits=httpx.Limits(max_keepalive_connections=8, keepalive_expiry=60),
        )
    return _http


async def _fetch(path: str, track: Track, quality: int) -> str:
    """One download attempt. Returns '' on success, or the failure reason.
    Writes to <path>.part and renames when complete, so a half-written file is never played."""
    params = {"key": MUSIC_API_KEY, "type": "video" if track.video else "audio", "quality": quality}
    timeout = httpx.Timeout(max(MUSIC_API_TIMEOUT, 600) if track.video else MUSIC_API_TIMEOUT, connect=20)
    part = path + ".part"
    try:
        async with _client().stream("GET", f"{MUSIC_API_URL}/stream/{track.vid}",
                                    params=params, timeout=timeout) as r:
            if r.status_code != 200:
                body = (await r.aread())[:150].decode("utf-8", "ignore").strip()
                return f"HTTP {r.status_code} {body}"
            with open(part, "wb") as f:
                async for chunk in r.aiter_bytes(262144):
                    f.write(chunk)
        if os.path.getsize(part) > 10000:
            os.replace(part, path)
            return ""
        return "API returned an empty file"
    except Exception as e:
        return f"{type(e).__name__} {e}".strip()
    finally:
        if os.path.exists(part):
            try:
                os.remove(part)
            except OSError:
                pass


_inflight: dict = {}      # path -> running download task (shared by prefetch + play)
_bg: set = set()
_cleaned = False


def _cleanup_old(max_age: int = 3 * 3600):
    """Once per start: remove leftovers of earlier runs from the downloads folder."""
    global _cleaned
    if _cleaned:
        return
    _cleaned = True
    try:
        now = time.time()
        for name in os.listdir(DOWNLOAD_DIR):
            fp = os.path.join(DOWNLOAD_DIR, name)
            if os.path.isfile(fp) and now - os.path.getmtime(fp) > max_age:
                os.remove(fp)
    except OSError:
        pass


async def _download(track: Track, path: str) -> str:
    reason = ""
    for q in (MUSIC_API_VIDEO_QUALITY if track.video else MUSIC_API_QUALITY):
        reason = await _fetch(path, track, q)
        if not reason:
            return path
        log.warning("music API %s q=%s failed: %s", track.vid, q, _scrub(reason))
    raise StreamError(f"music API failed ({_scrub(reason)})")


def _cacheable(track: Track) -> bool:
    return cache.enabled and bool(track.vid) and not track.video      # audio only


async def _acquire(track: Track, path: str) -> str:
    """Get the file at `path`: from the Firebase cache if it is there, otherwise download it
    from the API ONCE and save it to the cache for next time."""
    if _cacheable(track) and await cache.fetch(track.vid, path):
        return path
    await _download(track, path)
    if _cacheable(track):
        cache.store_bg(track.vid, path, track.title)
    return path


async def prepare(track: Track) -> str:
    """Download the track through the third-party API; returns the file path.
    If the same file is already downloading (prefetch), this just waits for it."""
    if track.stream_url:                 # live radio: nothing to download
        return track.stream_url
    if not API_ENABLED:
        raise StreamError("MUSIC_API_KEY is not set")
    if not track.vid:
        raise StreamError("missing video id")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    _cleanup_old()
    ext = "mp4" if track.video else "mp3"
    path = os.path.join(DOWNLOAD_DIR, f"{track.vid}.{ext}")
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        track.file_path = path
        return path
    task = _inflight.get(path)
    if task is None:
        task = asyncio.create_task(_acquire(track, path))
        _inflight[path] = task
        task.add_done_callback(lambda _t, p=path: _inflight.pop(p, None))
    await asyncio.shield(task)          # a cancelled caller must not kill a shared download
    track.file_path = path
    return path


def _direct_url(track: Track) -> str:
    """URL ffmpeg can read right away (the API streams the audio while it is prepared)."""
    q = (MUSIC_API_VIDEO_QUALITY if track.video else MUSIC_API_QUALITY)[0]
    return (f"{MUSIC_API_URL}/stream/{track.vid}?key={MUSIC_API_KEY}"
            f"&type={'video' if track.video else 'audio'}&quality={q}")


async def source(track: Track) -> tuple:
    """Where to read this track from -> (path_or_url, is_direct_stream).

    Order: live radio URL  >  finished download  >  a download that is nearly done  >
    Firebase song cache  >  the API stream itself (first play ever: starts at once while
    the song is downloaded + saved to the cache in the background)  >  download."""
    if track.stream_url:
        return track.stream_url, True
    path = await _ready_file(track)
    if path:
        return path, False
    if _cacheable(track) and await cache.has(track.vid):        # saved in Firebase: no API call
        return await prepare(track), False
    if MUSIC_DIRECT_STREAM and API_ENABLED and track.vid and not track.video and not track.force_dl:
        prefetch(track)               # start playing now AND save the song once for next time
        return _direct_url(track), True
    return await prepare(track), False


async def _ready_file(track: Track) -> str:
    if not track.vid or not API_ENABLED:
        return ""
    ext = "mp4" if track.video else "mp3"
    path = os.path.join(DOWNLOAD_DIR, f"{track.vid}.{ext}")
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        track.file_path = path
        return path
    task = _inflight.get(path)
    if task is not None:                 # being prefetched: if it's about to finish, use the file
        try:
            await asyncio.wait_for(asyncio.shield(task), 2)
            if os.path.exists(path):
                track.file_path = path
                return path
        except Exception:
            pass
    return ""


def prefetch(track: Track) -> None:
    """Start downloading a track in the background (fire and forget)."""
    if not API_ENABLED or not track.vid or track.stream_url:
        return

    async def _go():
        try:
            await prepare(track)
        except Exception as e:
            log.info("prefetch %s failed: %s", track.vid, _scrub(str(e)))

    t = asyncio.create_task(_go())
    _bg.add(t)
    t.add_done_callback(_bg.discard)


def release(track, still_needed=()) -> None:
    """Delete a track's downloaded file unless another queued track uses it."""
    path = getattr(track, "file_path", "")
    if not path or any(t is not track and t.file_path == path for t in still_needed):
        return
    try:
        os.remove(path)
    except OSError:
        pass
    track.file_path = ""


# ---------------------------------------------------------------- similar songs
_NOISE = re.compile(r"[\(\[].*?[\)\]]|official|video|lyrics?|audio|full song|hd|4k", re.I)


async def related_tracks(track, exclude_vids, limit: int = 16, user: str = "Rec") -> list:
    """Songs similar to `track` (same artist/channel first), never one in exclude_vids."""
    from py_yt import VideosSearch
    base = " ".join(_NOISE.sub(" ", track.title).split()[:5])
    queries = []
    if track.channel:
        queries.append(f"{track.channel} songs")
    queries.append(f"{base} similar songs")
    out, seen = [], set(exclude_vids) | {track.vid}
    for q in queries:
        try:
            res = (await asyncio.wait_for(VideosSearch(q, limit=20).next(), 10)).get("result") or []
        except Exception:
            continue
        for r in res:
            if not r.get("id") or r["id"] in seen:
                continue
            if not 60 <= _dur_secs(r.get("duration")) <= 600:
                continue
            seen.add(r["id"])
            out.append(_to_track(r, track.video, user))
            if len(out) >= limit:
                return out
    return out


async def related_track(track, exclude_vids, user="Autoplay"):
    """One random similar song (used by autoplay). None if nothing fits."""
    found = await related_tracks(track, exclude_vids, limit=8, user=user)
    return random.choice(found[:5]) if found else None


def fmt_time(seconds: int) -> str:
    if not seconds:
        return "LIVE"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
