# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music SETTINGS  (edit this file, or use env vars)
# ============================================================
# Every value can be set here OR as an environment variable.

import os

# Session string of a SPARE Telegram user account (the "assistant" that joins
# voice chats). Blank = music system disabled.
STRING_SESSION = os.getenv("STRING_SESSION", "")

# Limits
MUSIC_DURATION_LIMIT = int(os.getenv("MUSIC_DURATION_LIMIT", 180))  # minutes per track, 0 = no limit
MUSIC_QUEUE_LIMIT = int(os.getenv("MUSIC_QUEUE_LIMIT", 20))         # tracks per group

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
# 192 kbps sounds the same as 320 after Telegram's voice-chat encoding but downloads
# ~40% faster. Put 320 first (MUSIC_API_QUALITY=320,192,128) if you prefer max size.
MUSIC_API_QUALITY = _qualities("MUSIC_API_QUALITY", "192,128,320")
MUSIC_API_VIDEO_QUALITY = _qualities("MUSIC_API_VIDEO_QUALITY", "480,360")

# Small text in the corner of the generated "now playing" thumbnail
MUSIC_BRAND = os.getenv("MUSIC_BRAND", "ᴇʟɪɴᴀ ᴍᴜsɪᴄ")
