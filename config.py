# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Config
# ============================================================
import os
from dotenv import load_dotenv

load_dotenv()

# ---- Telegram API (from https://my.telegram.org) ----
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# ---- Database: Firebase Realtime Database ----
# Only used for welcome settings and music favourites.
FIREBASE_URL = os.getenv("FIREBASE_URL", "").rstrip("/")
FIREBASE_SECRET = os.getenv("FIREBASE_SECRET", "")

# ---- Owner / Bot info ----
OWNER_ID = int(os.getenv("OWNER_ID", 0))
BOT_NAME = os.getenv("BOT_NAME", "ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪")

# ---- Logger group/channel (new-group / removed-group notices + broadcast logs) ----
# Put the ID of a group or channel where the bot is admin, e.g. -1001234567890. 0 = disabled.
LOGGER_ID = int(os.getenv("LOGGER_ID", 0))
# Photo shown in logger messages (direct image URL or file_id). Empty = text only.
START_IMG = os.getenv("START_IMG", "")

# ---- Extra owners ----
# Telegram user IDs (comma or space separated) who may use the owner commands
# (/broadcast, /setstring, /delstring, /link ...) exactly like OWNER_ID.
# Env name: AUTH_USER (AUTH_USERS also works).   Example: AUTH_USER=123456789,987654321
def _ids(*names) -> list:
    out = []
    for name in names:
        for part in os.getenv(name, "").replace(",", " ").replace(";", " ").split():
            if part.lstrip("-").isdigit():
                out.append(int(part))
    return out


AUTH_USERS = _ids("AUTH_USER", "AUTH_USERS")


def is_owner(user_id) -> bool:
    """True for OWNER_ID and everyone listed in AUTH_USER."""
    return bool(user_id) and (user_id == OWNER_ID or user_id in AUTH_USERS)
