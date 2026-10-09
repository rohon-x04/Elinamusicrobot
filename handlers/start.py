# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - /start and /help  (photo + coloured buttons)
# All texts, labels, colours and links are in strings.py - edit them there.
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
from handlers.colorui import colorize, edit_styled

ADD_RIGHTS = "delete_messages+invite_users+pin_messages+manage_video_chats"


def _build(rows):
    """rows = [[(button, colour[, icon_id]), ...], ...]  ->  (markup, styles, icons)"""
    markup = M([[item[0] for item in row] for row in rows])
    styles = [[item[1] for item in row] for row in rows]
    icons = [[(item[2] if len(item) > 2 else "") for item in row] for row in rows]
    return markup, styles, icons


def _label(text: str, icon: str, emoji: str) -> str:
    """Plain emoji in front of the text, unless a premium icon id is used instead."""
    return text if icon or not emoji else f"{emoji} {text}"


def _start_ui(username: str):
    rows = [
        [(B(_label(S.BTN_ADD, S.ICON_ADD, S.EMOJI_ADD), url=f"https://t.me/{username}?startgroup=true&admin={ADD_RIGHTS}"), "success", S.ICON_ADD)],
        [(B(_label(S.BTN_HELP, S.ICON_HELP, S.EMOJI_HELP), callback_data="help:main"), "primary", S.ICON_HELP)],
    ]
    row = []
    if S.SUPPORT_CHAT_URL:
        row.append((B(S.BTN_SUPPORT, url=S.SUPPORT_CHAT_URL), "success"))
    if S.SUPPORT_CHANNEL_URL:
        row.append((B(S.BTN_UPDATES, url=S.SUPPORT_CHANNEL_URL), "primary"))
    if row:
        rows.append(row)
    row = []
    if S.OWNER_URL:
        row.append((B(S.BTN_OWNER, url=S.OWNER_URL), "success"))
    row.append((B(_label(S.BTN_CLOSE, S.ICON_CLOSE, S.EMOJI_CLOSE), callback_data="help:close"), "danger", S.ICON_CLOSE))
    rows.append(row)
    return _build(rows)


def _help_ui():
    rows, row = [], []
    for key, label, colour in S.HELP_CATEGORIES:
        row.append((B(label, callback_data=f"help:cat:{key}"), colour))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([(B(S.BTN_BACK, callback_data="help:start"), "primary")])
    return _build(rows)


def _back_ui():
    return _build([[(B(S.BTN_BACK, callback_data="help:main"), "success")]])


def _help_text() -> str:
    if S.SUPPORT_CHAT_URL:
        support = f'<a href="{S.SUPPORT_CHAT_URL}">{S.HELP_SUPPORT_TEXT}</a>'
    else:
        support = S.HELP_SUPPORT_TEXT
    return S.HELP_MAIN.format(support)


def _start_text(user) -> str:
    return S.START_PM.format(html.escape(user.first_name or "User"), html.escape(BOT_NAME))


async def _send(message, text: str, ui):
    """Photo + caption when START_IMG works, plain text otherwise; then colour the buttons."""
    markup, styles, icons = ui
    sent = None
    if START_IMG:
        try:
            sent = await message.reply_photo(START_IMG, caption=text, reply_markup=markup,
                                             parse_mode=ParseMode.HTML)
        except Exception as e:
            logging.info(f"start photo failed, sending text: {e}")
    if sent is None:
        sent = await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML,
                                        disable_web_page_preview=True)
    await colorize(sent, markup, styles, icons)
    return sent


async def _show(query, text: str, ui):
    """Edit the menu in place (caption for photo menus) keeping the colours."""
    markup, styles, icons = ui
    if await edit_styled(query.message, text, markup, styles, parse_mode="HTML", icons=icons):
        return
    try:
        if query.message.photo:
            await query.message.edit_caption(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        else:
            await query.message.edit_text(text, reply_markup=markup, parse_mode=ParseMode.HTML,
                                          disable_web_page_preview=True)
    except MessageNotModified:
        pass
    await colorize(query.message, markup, styles, icons)


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

    def _pm_button(username):
        return _build([[(B(S.BTN_OPEN_PM, url=f"https://t.me/{username}?start=help"), "primary")]])

    @app.on_message(filters.command("start"))
    async def start_cmd(client, message):
        username = client.me.username

        # ---- group: short message ----
        if message.chat.type != ChatType.PRIVATE:
            try:
                await message.delete()
            except Exception:
                pass
            try:
                await _send(message, S.START_GP.format(html.escape(BOT_NAME)), _pm_button(username))
            except Exception:
                pass
            return

        # ---- private ----
        if not message.from_user:
            return
        await _notify_new_user(client, message.from_user)

        if len(message.command) > 1 and message.command[1] == "help":
            return await _send(message, _help_text(), _help_ui())
        await _send(message, _start_text(message.from_user), _start_ui(username))

    @app.on_message(filters.command("help"))
    async def help_cmd(client, message):
        if message.chat.type != ChatType.PRIVATE:
            return await _send(message, S.START_GP.format(html.escape(BOT_NAME)),
                               _pm_button(client.me.username))
        await _send(message, _help_text(), _help_ui())

    @app.on_callback_query(filters.regex(r"^help:"))
    async def help_cb(client, query):
        parts = query.data.split(":")
        action = parts[1]
        if action == "main":
            await _show(query, _help_text(), _help_ui())
        elif action == "cat" and len(parts) > 2 and parts[2] in S.HELP_PAGES:
            await _show(query, S.HELP_PAGES[parts[2]], _back_ui())
        elif action == "start":
            await _show(query, _start_text(query.from_user), _start_ui(client.me.username))
        elif action == "close":
            try:
                await query.message.delete()
            except Exception:
                pass
            return
        await query.answer()
