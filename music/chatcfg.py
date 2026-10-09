# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: per-group admin settings
# ============================================================
#   playmode   all | admins     who may use /play, /vplay, /radio
#   skipmode   all | admins     who may /skip (default = MUSIC_FREE_SKIP)
#   auth       user ids         "authorised users" - may control music without being admin
# Kept in memory and saved to Firebase (if configured) so they survive restarts.

import logging
from dataclasses import dataclass, field

from .settings import MUSIC_FREE_SKIP

log = logging.getLogger("music")


@dataclass
class ChatCfg:
    playmode: str = "all"
    skipmode: str = "all" if MUSIC_FREE_SKIP else "admins"
    auth: set = field(default_factory=set)


_cfg: dict = {}


async def get(chat_id: int) -> ChatCfg:
    cfg = _cfg.get(chat_id)
    if cfg is not None:
        return cfg
    cfg = ChatCfg()
    try:
        import db
        data = await db.get_music_cfg(chat_id)
        if data.get("playmode") in ("all", "admins"):
            cfg.playmode = data["playmode"]
        if data.get("skipmode") in ("all", "admins"):
            cfg.skipmode = data["skipmode"]
        cfg.auth = {int(k) for k in (data.get("auth") or {}) if str(k).lstrip("-").isdigit()}
    except Exception as e:                  # no database / offline: defaults, kept in memory
        log.info("music cfg for %s not loaded: %s", chat_id, e)
    _cfg[chat_id] = cfg
    return cfg


async def set_mode(chat_id: int, key: str, value: str):
    cfg = await get(chat_id)
    setattr(cfg, key, value)
    try:
        import db
        await db.set_music_cfg(chat_id, key, value)
    except Exception as e:
        log.warning("could not save %s for %s: %s", key, chat_id, e)


async def set_auth(chat_id: int, user_id: int, on: bool):
    cfg = await get(chat_id)
    (cfg.auth.add if on else cfg.auth.discard)(user_id)
    try:
        import db
        await db.set_music_auth(chat_id, user_id, on)
    except Exception as e:
        log.warning("could not save auth list for %s: %s", chat_id, e)
