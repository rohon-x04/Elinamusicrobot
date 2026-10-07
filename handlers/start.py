# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - /start and /help (photo + buttons)
# All texts, labels and links are in strings.py - edit them there.
# The photo comes from START_IMG in .env (empty = text only).
# ============================================================
import html
import logging

from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M

import db
import strings as S
from config import BOT_NAME, START_IMG, LOGGER_ID

ADD_RIGHTS = "delete_messages+invite_users+pin_messages+manage_video_chats"


def _start_markup(username: str) -> M:
    rows = [
        [B(S.BTN_ADD, url=f"https://t.me/{username}?startgroup=true&admin={ADD_RIGHTS}")],
        [B(S.BTN_HELP, callback_data="help:main")],
    ]
    extra = []
    if S.SUPPORT_CHAT_URL:
        extra.append(B(S.BTN_SUPPORT, url=S.SUPPORT_CHAT_URL))
    if S.SUPPORT_CHANNEL_URL:
        extra.append(B(S.BTN_CHANNEL, url=S.SUPPORT_CHANNEL_URL))
    if extra:
        rows.append(extra)
    if S.OWNER_URL:
        rows.append([B(S.BTN_OWNER, url=S.OWNER_URL)])
    return M(rows)


def _help_main_markup() -> M:
    return M([
        [B(S.BTN_MUSIC, callback_data="help:music"), B(S.BTN_WELCOME, callback_data="help:welcome")],
        [B(S.BTN_OWNER_CMDS, callback_data="help:owner")],
        [B(S.BTN_BACK, callback_data="help:start"), B(S.BTN_CLOSE, callback_data="help:close")],
    ])


def _back_markup() -> M:
    return M([[B(S.BTN_BACK, callback_data="help:main")]])


async def _reply(message, text: str, markup: M, with_photo: bool = True):
    """Photo + caption when START_IMG works, plain text otherwise."""
    if with_photo and START_IMG:
        try:
            return await message.reply_photo(START_IMG, caption=text, reply_markup=markup,
                                             parse_mode=ParseMode.HTML)
        except Exception as e:
            logging.info(f"start photo failed, sending text: {e}")
    return await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML,
                                    disable_web_page_preview=True)


async def _edit(query, text: str, markup: M):
    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML,
                                          disable_web_page_preview=True)
    except MessageNotModified:
        pass


async def _notify_new_user(client, user):
    """First time this person starts the bot: remember them + tell the log chat."""
    if await db.is_user(user.id):
        return
    await db.add_user(user.id)
    if LOGGER_ID:
        try:
            await client.send_message(
                LOGGER_ID,
                S.NEW_USER_LOG.format(
                    f'<a href="tg://user?id={user.id}">{html.escape(user.first_name or "User")}</a>',
                    user.id,
                    f"@{user.username}" if user.username else S.UNKNOWN,
                ),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass


def register_start_handlers(app: Client):

    @app.on_message(filters.command("start"))
    async def start_cmd(client, message):
        username = client.me.username

        # ---- group: short message ----
        if message.chat.type != ChatType.PRIVATE:
            try:
                await message.delete()
            except Exception:
                pass
            markup = M([[B(S.BTN_OPEN_PM, url=f"https://t.me/{username}?start=help")]])
            try:
                await _reply(message, S.START_GP.format(html.escape(BOT_NAME)), markup)
            except Exception:
                pass
            return

        # ---- private ----
        if not message.from_user:
            return
        await _notify_new_user(client, message.from_user)

        if len(message.command) > 1 and message.command[1] == "help":
            return await _reply(message, S.HELP_MAIN, _help_main_markup())

        await _reply(
            message,
            S.START_PM.format(html.escape(message.from_user.first_name or "User"),
                              html.escape(BOT_NAME)),
            _start_markup(username),
        )

    @app.on_message(filters.command("help"))
    async def help_cmd(client, message):
        if message.chat.type != ChatType.PRIVATE:
            markup = M([[B(S.BTN_OPEN_PM, url=f"https://t.me/{client.me.username}?start=help")]])
            return await message.reply_text(S.START_GP.format(html.escape(BOT_NAME)),
                                            reply_markup=markup, parse_mode=ParseMode.HTML)
        await _reply(message, S.HELP_MAIN, _help_main_markup())

    @app.on_callback_query(filters.regex(r"^help:"))
    async def help_cb(client, query):
        action = query.data.split(":", 1)[1]
        if action == "main":
            await _edit(query, S.HELP_MAIN, _help_main_markup())
        elif action == "music":
            await _edit(query, S.HELP_MUSIC, _back_markup())
        elif action == "welcome":
            await _edit(query, S.HELP_WELCOME, _back_markup())
        elif action == "owner":
            await _edit(query, S.HELP_OWNER, _back_markup())
        elif action == "start":
            await _edit(
                query,
                S.START_PM.format(html.escape(query.from_user.first_name or "User"),
                                  html.escape(BOT_NAME)),
                _start_markup(client.me.username),
            )
        elif action == "close":
            try:
                await query.message.delete()
            except Exception:
                pass
            return
        await query.answer()
