# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Broadcast to groups and DMs (owner only)
#
#   /broadcast <text>            send text to all groups
#   /broadcast (reply to msg)    forward that message to all groups
#   options:  -user   also send to users (DM)
#             -nochat skip groups
#             -copy   send as a copy (no "forwarded from" tag)
#             -pin    pin the message in groups
#   /stop_gcast                  stop a running broadcast
# Texts live in strings.py - edit them there.
# ============================================================
import asyncio
import logging

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import (
    FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid,
    ChatWriteForbidden, ChannelPrivate, ChatIdInvalid, ChatAdminRequired,
    UserDeactivated, UserDeactivatedBan,
)

import db
import strings as S
from handlers.common import NO_PREVIEW
from config import LOGGER_ID, is_owner

DELAY = 0.25          # seconds between sends (stay under Telegram flood limits)
FLAGS = {"-user", "-nochat", "-copy", "-pin"}

_running = False
_stop = False


def _parse(message):
    """Return (flags, text_after_flags)."""
    parts = (message.text or "").split()[1:]
    flags = {p.lower() for p in parts if p.lower() in FLAGS}
    text = " ".join(p for p in parts if p.lower() not in FLAGS)
    return flags, text


async def _send_one(client, chat_id, src, text, copy, pin):
    """Send to one chat. Returns the sent Message. Handles FloodWait once."""
    for _ in range(2):
        try:
            if src is not None:
                return await (src.copy(chat_id) if copy else src.forward(chat_id))
            return await client.send_message(chat_id, text, parse_mode=ParseMode.HTML,
                                             **NO_PREVIEW)
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
    raise RuntimeError("flood")


async def _run(client, message, flags, text, src):
    global _running, _stop
    _running, _stop = True, False
    sent_g = sent_u = failed = 0
    copy = "-copy" in flags
    pin = "-pin" in flags
    try:
        chats = [] if "-nochat" in flags else await db.get_all_chats()
        users = await db.get_all_users() if "-user" in flags else []

        await message.reply_text(S.GCAST_START.format(len(chats) + len(users)),
                                 parse_mode=ParseMode.HTML)

        # ---- groups ----
        for chat_id in chats:
            if _stop:
                break
            try:
                sent = await _send_one(client, chat_id, src, text, copy, pin)
                sent_g += 1
                if pin and sent:
                    try:
                        await sent.pin(disable_notification=True)
                    except Exception:
                        pass
            except (ChatWriteForbidden, ChannelPrivate, ChatIdInvalid, PeerIdInvalid):
                failed += 1
                await db.remove_chat(chat_id)      # bot was kicked / can't write
            except Exception as e:
                failed += 1
                logging.info(f"broadcast: group {chat_id} failed: {e}")
            await asyncio.sleep(DELAY)

        # ---- users ----
        for user_id in users:
            if _stop:
                break
            try:
                await _send_one(client, user_id, src, text, copy, False)
                sent_u += 1
            except (UserIsBlocked, InputUserDeactivated, UserDeactivated,
                    UserDeactivatedBan, PeerIdInvalid):
                failed += 1
                await db.remove_user(user_id)      # blocked / deleted account
            except Exception as e:
                failed += 1
                logging.info(f"broadcast: user {user_id} failed: {e}")
            await asyncio.sleep(DELAY)

        tpl = S.GCAST_STOPPED if _stop else S.GCAST_END
        await message.reply_text(tpl.format(sent_g, sent_u, failed), parse_mode=ParseMode.HTML)
    except Exception as e:
        logging.exception("broadcast crashed")
        await message.reply_text(f"❌ Broadcast error:\n<code>{e}</code>", parse_mode=ParseMode.HTML)
    finally:
        _running = False


def register_broadcast_handlers(app: Client):

    @app.on_message(filters.command(["broadcast", "gcast"]))
    async def broadcast_cmd(client, message):
        if not (message.from_user and is_owner(message.from_user.id)):
            return await message.reply_text(S.GCAST_NOT_OWNER, parse_mode=ParseMode.HTML)
        if _running:
            return await message.reply_text(S.GCAST_ACTIVE, parse_mode=ParseMode.HTML)

        flags, text = _parse(message)
        src = message.reply_to_message
        if src is None and not text:
            return await message.reply_text(S.GCAST_USAGE, parse_mode=ParseMode.HTML)

        if LOGGER_ID:
            try:
                await client.send_message(
                    LOGGER_ID,
                    S.GCAST_LOG.format(message.from_user.id, message.from_user.first_name,
                                       (message.text or "")[:200]),
                    parse_mode=ParseMode.HTML)
            except Exception:
                pass

        # run in background so the bot keeps answering while broadcasting
        asyncio.create_task(_run(client, message, flags, text, src))

    @app.on_message(filters.command(["stop_gcast", "stopbroadcast"]))
    async def stop_cmd(client, message):
        global _stop
        if not (message.from_user and is_owner(message.from_user.id)):
            return await message.reply_text(S.GCAST_NOT_OWNER, parse_mode=ParseMode.HTML)
        if not _running:
            return await message.reply_text(S.GCAST_INACTIVE, parse_mode=ParseMode.HTML)
        _stop = True
        await message.reply_text(S.GCAST_STOP, parse_mode=ParseMode.HTML)
