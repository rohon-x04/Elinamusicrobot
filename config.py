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
