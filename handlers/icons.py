# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Button icons + start-button links (shared state)
# Icons: saved with  /emojiid set  (database) or ICON_* in .env / strings.py.
# Links: Support / Updates / Owner. Missing ones fall back so the layout is always complete.
# ============================================================
import logging
import time

import db
import strings as S
from config import OWNER_ID
from handlers.common import clean_url

DEFAULT_ICONS = {"add": S.ICON_ADD, "help": S.ICON_HELP, "close": S.ICON_CLOSE}
ICONS = dict(DEFAULT_ICONS)                       # what the buttons use right now
LINKS = {"support": "", "updates": "", "owner": ""}

_loaded_at = 0.0
_owner_cache = ""


async def prepare(client, force: bool = False):
    """Refresh icons and links (at most once a minute)."""
    global _loaded_at, _owner_cache
    now = time.monotonic()
    if not force and _loaded_at and now - _loaded_at < 60:
        return
    _loaded_at = now

    # icons: database value wins, otherwise .env / strings.py
    try:
        saved = await db.get_icons()
    except Exception as e:
        logging.info(f"icons: could not read database ({e})")
        saved = {}
    for key, default in DEFAULT_ICONS.items():
        ICONS[key] = str(saved.get(key) or default or "")

    # links
    owner = clean_url(S.OWNER_URL)
    if not owner and OWNER_ID:
        if not _owner_cache:
            try:
                user = await client.get_users(OWNER_ID)
                _owner_cache = f"https://t.me/{user.username}" if user.username else ""
            except Exception:
                pass
        owner = _owner_cache
    chat, channel = clean_url(S.SUPPORT_CHAT_URL), clean_url(S.SUPPORT_CHANNEL_URL)
    LINKS["owner"] = owner
    LINKS["support"] = chat or owner or channel
    LINKS["updates"] = channel or chat or owner


async def save_icons(add: str, help_: str, close: str):
    await db.set_icons({"add": add, "help": help_, "close": close})
    ICONS.update(add=add, help=help_, close=close)


async def reset_icons():
    await db.delete_icons()
    ICONS.update(DEFAULT_ICONS)
