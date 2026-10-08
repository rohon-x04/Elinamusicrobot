# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Colourful inline buttons
# ============================================================
#
# Telegram's Bot API (Feb 2026+) lets inline buttons carry a "style":
#   primary = blue, success = green, danger = red.
# Pyrogram 2.0.x talks MTProto and cannot send that field, so the menu
# is sent/edited by pyrogram as usual (plain buttons show up instantly)
# and this helper then re-sends the SAME keyboard through the Bot API
# with colours added. If that call ever fails, the plain buttons simply
# stay - nothing breaks.
# ============================================================

import logging

import httpx
from pyrogram.types import InlineKeyboardMarkup

from config import BOT_TOKEN

log = logging.getLogger(__name__)

_CYCLE = ("primary", "success", "danger")  # blue, green, red



_HTTP = None


def _http():
    """One shared client = keep-alive connections (no new TLS handshake per edit)."""
    global _HTTP
    if _HTTP is None or _HTTP.is_closed:
        _HTTP = httpx.AsyncClient(timeout=10, limits=httpx.Limits(max_keepalive_connections=10,
                                                                   keepalive_expiry=60))
    return _HTTP

def _style_for(btn, row: int, col: int, styles):
    if styles:
        try:
            return styles[row][col]
        except (IndexError, TypeError):
            pass
    if "Back" in (btn.text or ""):
        return "danger"
    return _CYCLE[(row + col) % 3]


def _to_api(markup: InlineKeyboardMarkup, styles=None) -> dict:
    rows = []
    for r, row in enumerate(markup.inline_keyboard):
        out = []
        for c, btn in enumerate(row):
            item = {"text": btn.text, "style": _style_for(btn, r, c, styles)}
            if btn.url:
                item["url"] = btn.url
            elif btn.callback_data is not None:
                data = btn.callback_data
                item["callback_data"] = data.decode() if isinstance(data, bytes) else data
            else:
                continue
            out.append(item)
        rows.append(out)
    return {"inline_keyboard": rows}


class StyledMessage:
    """Stand-in for a message that was already edited WITH coloured buttons in a
    single Bot API call - colorize() sees `styled` and does nothing more."""

    styled = True

    def __init__(self, message):
        self.chat = message.chat
        self.id = message.id
        self.photo = getattr(message, "photo", None)
        self.caption = getattr(message, "caption", None)


async def edit_styled(message, text: str, markup: InlineKeyboardMarkup, styles=None,
                      parse_mode=None) -> bool:
    """Change a menu message's caption (photo menu) or text AND its coloured
    buttons in ONE Bot API call, so the buttons never flash plain/olive between
    two edits. Returns True on success; False means 'use the normal pyrogram
    edit instead' (nothing was changed)."""
    if not BOT_TOKEN or message is None:
        return False
    media = bool(getattr(message, "photo", None)) or getattr(message, "caption", None) is not None
    payload = {
        "chat_id": message.chat.id,
        "message_id": message.id,
        "reply_markup": _to_api(markup, styles),
    }
    payload["caption" if media else "text"] = text
    if not media:
        payload["link_preview_options"] = {"is_disabled": True}   # no YouTube preview under the text
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        resp = await _http().post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/"
            + ("editMessageCaption" if media else "editMessageText"),
            json=payload,
        )
        if resp.status_code == 200 or "message is not modified" in resp.text:
            return True
        log.warning("Styled edit failed: %s", resp.text[:200])
    except Exception:
        log.warning("Styled edit failed", exc_info=True)
    return False


async def colorize(message, markup: InlineKeyboardMarkup, styles=None):
    """Re-apply `markup` to `message` with coloured buttons.
    `styles` (optional) is a nested list matching the keyboard layout,
    e.g. [["success"], ["primary", "danger"]]; otherwise colours cycle
    blue/green/red and any "Back" button is red."""
    if not BOT_TOKEN or message is None or getattr(message, "styled", False):
        return
    try:
        resp = await _http().post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/editMessageReplyMarkup",
            json={
                "chat_id": message.chat.id,
                "message_id": message.id,
                "reply_markup": _to_api(markup, styles),
            },
        )
        if resp.status_code != 200:
            log.warning("Button colour update failed: %s", resp.text[:200])
    except Exception:
        log.warning("Button colour update failed", exc_info=True)
