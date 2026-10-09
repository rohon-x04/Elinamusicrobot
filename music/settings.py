# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music SETTINGS  (edit this file, or use env vars)
# ============================================================
# Every value can be set here OR as an environment variable.

import os

# Session string of a SPARE Telegram user account (the "assistant" that joins
# voice chats). Blank = music system disabled.
STRING_SESSION = os.getenv("STRING_SESSION", "")


def _sessions() -> list:
    """Every assistant session from the env: STRING_SESSION, STRING_SESSION2..STRING_SESSION9
    and/or STRING_SESSIONS (comma / space separated). Duplicates are dropped."""
    names = ["STRING_SESSION"] + [f"STRING_SESSION{i}" for i in range(2, 10)]
    out = []
    for n in names:
        v = os.getenv(n, "").strip().strip("\"'`")
        if v:
            out.append(v)
    for v in os.getenv("STRING_SESSIONS", "").replace(",", " ").split():
        v = v.strip().strip("\"'`")
        if v:
            out.append(v)
    seen, uniq = set(), []
    for v in out:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


# Multi-assistants: every session found in the env (more can be added live with /setstring)
STRING_SESSIONS = _sessions()

# Limits
MUSIC_DURATION_LIMIT = int(os.getenv("MUSIC_DURATION_LIMIT", 180))  # minutes per track, 0 = no limit
MUSIC_QUEUE_LIMIT = int(os.getenv("MUSIC_QUEUE_LIMIT", 50))         # tracks per group (smart queue: 30+)

# Who may change the song with /skip and the ⏭ button.
# 1 = admins AND members (default)   0 = admins only
MUSIC_FREE_SKIP = os.getenv("MUSIC_FREE_SKIP", "1").strip().lower() not in ("0", "false", "no", "off")

# Show a "songs similar to the track that just ended" picker when the queue
# finishes (and autoplay is off). 1 = yes, 0 = no.
MUSIC_SUGGEST_AFTER_END = os.getenv("MUSIC_SUGGEST_AFTER_END", "1").strip().lower() not in ("0", "false", "no", "off")

# ---- Third-party music API (the ONLY audio source) -------------------------
# Key from @MeowApiRobot on Telegram. Endpoint:
#   GET {URL}/stream/<youtube_id>?key=<key>&type=audio|video&quality=<n>
_DEFAULT_API_URL = "https://music.yukiapi.site"


def _clean_url(raw: str) -> str:
    raw = (raw or "").strip().strip("\"'").rstrip("/")
    if not raw or "." not in raw:
        return _DEFAULT_API_URL          # empty / not a real address -> default
    if not raw.lower().startswith(("http://", "https://")):
        raw = "https://" + raw           # scheme was forgotten
    return raw


def _qualities(env_name: str, default: str) -> list:
    out = []
    for part in os.getenv(env_name, default).replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            out.append(int(part))
    return out or [int(x) for x in default.split(",")]


MUSIC_API_URL = _clean_url(os.getenv("MUSIC_API_URL") or os.getenv("MEOW_API_URL") or "")
MUSIC_API_KEY = (os.getenv("MUSIC_API_KEY") or os.getenv("MEOW_API_KEY") or "").strip().strip("\"'")
if MUSIC_API_KEY == "YOUR_API_KEY":
    MUSIC_API_KEY = ""
MUSIC_API_TIMEOUT = int(os.getenv("MUSIC_API_TIMEOUT", 300))        # seconds per download

# Sound quality in order of preference. The bot asks for the first value; if the API
# doesn't have it, it tries the next one.   (kbps for audio, p for video)
# Songs now START STREAMING straight from the API (no waiting for a download), so the best
# quality (320) is the default. Use MUSIC_API_QUALITY=192,128 on a very slow connection.
MUSIC_API_QUALITY = _qualities("MUSIC_API_QUALITY", "320,192,128")
MUSIC_API_VIDEO_QUALITY = _qualities("MUSIC_API_VIDEO_QUALITY", "480,360")

# Small text in the corner of the generated "now playing" thumbnail
MUSIC_BRAND = os.getenv("MUSIC_BRAND", "ᴇʟɪɴᴀ ᴍᴜsɪᴄ")

# ---- Speed / quality ---------------------------------------------------------
def _flag(name: str, default: str = "1") -> bool:
    return os.getenv(name, default).strip().lower() not in ("0", "false", "no", "off")


# Lightning-fast start: audio is streamed straight from the API into ffmpeg while it
# downloads. Queued songs are still pre-downloaded so they start instantly.
MUSIC_DIRECT_STREAM = _flag("MUSIC_DIRECT_STREAM")

# Voice-chat audio profile handed to py-tgcalls (Telegram encodes it as Opus):
# STUDIO = 48 kHz stereo (best), HIGH, MEDIUM, LOW
MUSIC_AUDIO_QUALITY = os.getenv("MUSIC_AUDIO_QUALITY", "STUDIO").strip().upper()

# How many queued songs are pre-downloaded ahead of time
MUSIC_PREFETCH = max(1, int(os.getenv("MUSIC_PREFETCH", 2)))

# ---- Auto queue ---------------------------------------------------------------
# With autoplay ON the bot keeps the queue topped up with similar songs:
# whenever fewer than AUTO_MIN songs are waiting, AUTO_BATCH more are added.
MUSIC_AUTO_MIN = max(1, int(os.getenv("MUSIC_AUTO_MIN", 3)))
MUSIC_AUTO_BATCH = max(1, int(os.getenv("MUSIC_AUTO_BATCH", 5)))

# ---- Live radio ---------------------------------------------------------------
# Check the radio list in the background at start-up and hide dead stations (1 = yes)
MUSIC_RADIO_VALIDATE = _flag("MUSIC_RADIO_VALIDATE")
# Countries (ISO codes, comma separated) used to top the radio list up with the most
# popular live stations from radio-browser.info.
MUSIC_RADIO_COUNTRIES = [c.strip().upper() for c in
                         os.getenv("MUSIC_RADIO_COUNTRIES", "IN,US,GB").replace(" ", ",").split(",")
                         if c.strip()]

# ---- Song cache (Firebase) -----------------------------------------------------
# Every downloaded song is saved to your Firebase Realtime Database (FIREBASE_URL) once and
# played from there next time - the music API is not hit again for the same song.
# 1 = on (needs FIREBASE_URL), 0 = off.
MUSIC_CACHE = _flag("MUSIC_CACHE")
# Total cache size limit in MB. Realtime Database free plan = 1024 MB, so 800 is safe.
# When it is full the songs nobody played for the longest time are removed first.
MUSIC_CACHE_MAX_MB = max(50, int(os.getenv("MUSIC_CACHE_MAX_MB", 800)))
# Songs bigger than this (MB) are not cached (audio only - video is never cached)
MUSIC_CACHE_MAX_SONG_MB = max(1, int(os.getenv("MUSIC_CACHE_MAX_SONG_MB", 14)))
