# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - /ping  (status card with photo)
# Texts live in strings.py (PING_*). Works in groups and DM.
# ============================================================
import asyncio
import html
import logging
import os
import time

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M

import strings as S
from handlers.common import NO_PREVIEW, clean_url
from config import BOT_NAME, START_IMG
from handlers.colorui import colorize

_STARTED = time.time()


def _uptime() -> str:
    s = int(time.time() - _STARTED)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    return (f"{d}d:" if d else "") + f"{h}h:{m}m:{s}s"


def _system() -> tuple:
    """(ram_text, cpu_percent). Uses psutil when installed, /proc otherwise."""
    try:
        import psutil
        vm = psutil.virtual_memory()
        return f"{vm.used / 2**30:.1f}GB / {vm.total / 2**30:.1f}GB", psutil.cpu_percent(interval=0.4)
    except Exception:
        pass
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                info[k] = int(v.split()[0])
        total = info["MemTotal"] / 2**20
        used = total - info["MemAvailable"] / 2**20
        cpu = min(100.0, os.getloadavg()[0] / (os.cpu_count() or 1) * 100)
        return f"{used:.1f}GB / {total:.1f}GB", round(cpu, 1)
    except Exception:
        return "N/A", 0.0


def _calls_ping() -> float:
    try:
        from music import music_player
        if music_player.calls:
            return round(float(music_player.calls.ping), 3)
    except Exception:
        pass
    return 0.0


def _assistant_ready() -> bool:
    try:
        from music import music_player
        return bool(music_player.enabled)
    except Exception:
        return False


def register_ping_handlers(app: Client):

    @app.on_message(filters.command("ping"))
    async def ping_cmd(client, message):
        t0 = time.perf_counter()
        waiting = await message.reply_text(S.PING_WAIT, parse_mode=ParseMode.HTML)
        latency = round((time.perf_counter() - t0) * 1000, 2)

        ram, cpu = await asyncio.to_thread(_system)
        ok = _assistant_ready()
        text = S.PING_CARD.format(
            bot=html.escape(BOT_NAME),
            icon="✅" if ok else "⚠️",
            status=S.PING_STATUS_OK if ok else S.PING_STATUS_NO_ASSISTANT,
            latency=latency,
            uptime=_uptime(),
            calls=_calls_ping(),
            ram=ram,
            cpu=cpu,
            features="\n".join(f"• {f}" for f in S.PING_FEATURES),
            footer=S.PING_FOOTER,
        )

        # Updates (blue) + Support (green), only when the links are set in strings.py
        row, styles = [], []
        if clean_url(S.SUPPORT_CHANNEL_URL):
            row.append(B(S.BTN_UPDATES, url=clean_url(S.SUPPORT_CHANNEL_URL))); styles.append("primary")
        if clean_url(S.SUPPORT_CHAT_URL):
            row.append(B(S.BTN_SUPPORT, url=clean_url(S.SUPPORT_CHAT_URL))); styles.append("success")
        markup = M([row]) if row else None

        img = S.PING_IMG or START_IMG
        sent = None
        if img:
            try:
                sent = await message.reply_photo(img, caption=text, reply_markup=markup,
                                                 parse_mode=ParseMode.HTML)
            except Exception as e:
                logging.info(f"ping photo failed, sending text: {e}")
        if sent is None:
            sent = await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML,
                                            **NO_PREVIEW)
        if markup:
            await colorize(sent, markup, [styles])
        try:
            await waiting.delete()
        except Exception:
            pass
