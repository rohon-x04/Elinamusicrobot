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
from dataclasses import dataclass

import httpx

from .settings import (MUSIC_API_URL, MUSIC_API_KEY, MUSIC_API_TIMEOUT,
                       MUSIC_API_QUALITY, MUSIC_API_VIDEO_QUALITY)

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


async def search_track(query: str, video: bool, user: str) -> Track:
    """Find one song (by name or YouTube link). Raises LookupError if none."""
    from py_yt import VideosSearch
    results = await VideosSearch(query, limit=1).next()
    items = results.get("result") or []
    if not items:
        raise LookupError("nothing found")
    return _to_track(items[0], video, user)


# ---------------------------------------------------------------- API download
def _scrub(text: str) -> str:
    if MUSIC_API_KEY:
        text = text.replace(MUSIC_API_KEY, "***")
    return text


async def _fetch(path: str, track: Track, quality: int) -> str:
    """One download attempt. Returns '' on success, or the failure reason."""
    params = {"key": MUSIC_API_KEY, "type": "video" if track.video else "audio", "quality": quality}
    timeout = httpx.Timeout(max(MUSIC_API_TIMEOUT, 600) if track.video else MUSIC_API_TIMEOUT, connect=20)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as c:
            async with c.stream("GET", f"{MUSIC_API_URL}/stream/{track.vid}", params=params) as r:
                if r.status_code != 200:
                    body = (await r.aread())[:150].decode("utf-8", "ignore").strip()
                    return f"HTTP {r.status_code} {body}"
                with open(path, "wb") as f:
                    async for chunk in r.aiter_bytes(131072):
                        f.write(chunk)
        if os.path.getsize(path) > 10000:
            return ""
        return "API returned an empty file"
    except Exception as e:
        return f"{type(e).__name__} {e}".strip()


async def prepare(track: Track) -> str:
    """Download the track through the third-party API; returns the file path."""
    if not API_ENABLED:
        raise StreamError("MUSIC_API_KEY is not set")
    if not track.vid:
        raise StreamError("missing video id")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    ext = "mp4" if track.video else "mp3"
    path = os.path.join(DOWNLOAD_DIR, f"{track.vid}.{ext}")
    if os.path.exists(path) and os.path.getsize(path) > 10000:
        track.file_path = path
        return path
    reason = ""
    for q in (MUSIC_API_VIDEO_QUALITY if track.video else MUSIC_API_QUALITY):
        reason = await _fetch(path, track, q)
        if not reason:
            track.file_path = path
            return path
        log.warning("music API %s q=%s failed: %s", track.vid, q, _scrub(reason))
        try:
            os.remove(path)
        except OSError:
            pass
    raise StreamError(f"music API failed ({_scrub(reason)})")


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
            res = (await VideosSearch(q, limit=20).next()).get("result") or []
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
