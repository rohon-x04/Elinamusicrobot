# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - /start and /help  (photo + coloured buttons)
# All texts, labels, colours and links are in strings.py - edit them there.
# The photo comes from START_IMG in .env (empty = text only).
# ============================================================
import asyncio
import html
import logging

from pyrogram import Client, filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.errors import MessageNotModified
from pyrogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup as M

import db
import strings as S
from handlers.common import NO_PREVIEW, clean_url
from config import BOT_NAME, START_IMG, LOGGER_ID
from handlers.colorui import colorize, edit_styled
from handlers.icons import ICONS, LINKS, prepare

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
    """Same layout as the sample: Add / Help full width, [Support | Updates], [Owner | Close]."""
    rows = [
        [(B(_label(S.BTN_ADD, ICONS["add"], S.EMOJI_ADD),
            url=f"https://t.me/{username}?startgroup=true&admin={ADD_RIGHTS}"), "success", ICONS["add"])],
        [(B(_label(S.BTN_HELP, ICONS["help"], S.EMOJI_HELP), callback_data="help:main"),
          "primary", ICONS["help"])],
    ]
    row = []
    if LINKS["support"]:
        row.append((B(S.BTN_SUPPORT, url=LINKS["support"]), "success"))
    if LINKS["updates"]:
        row.append((B(S.BTN_UPDATES, url=LINKS["updates"]), "primary"))
    if row:
        rows.append(row)
    row = []
    if LINKS["owner"]:
        row.append((B(S.BTN_OWNER, url=LINKS["owner"]), "success"))
    row.append((B(_label(S.BTN_CLOSE, ICONS["close"], S.EMOJI_CLOSE), callback_data="help:close"),
                "danger", ICONS["close"]))
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
    if clean_url(S.SUPPORT_CHAT_URL):
        support = f'<a href="{clean_url(S.SUPPORT_CHAT_URL)}">{S.HELP_SUPPORT_TEXT}</a>'
    else:
        support = S.HELP_SUPPORT_TEXT
    return S.HELP_MAIN.format(support)


def _start_text(user) -> str:
    return S.START_PM.format(html.escape(user.first_name or "User"), html.escape(BOT_NAME))


def _variants(ui):
    """Layouts to try, best first. If Telegram rejects a button link we fall back step by step
    instead of leaving the user without any reply."""
    markup, styles, icons = ui

    def rebuild(transform):
        rows, st, ic = [], [], []
        for r, row in enumerate(markup.inline_keyboard):
            new_row, new_st, new_ic = [], [], []
            for c, btn in enumerate(row):
                nb = transform(btn)
                if nb is None:
                    continue
                new_row.append(nb); new_st.append(styles[r][c]); new_ic.append(icons[r][c])
            if new_row:
                rows.append(new_row); st.append(new_st); ic.append(new_ic)
        return (M(rows) if rows else None), st, ic

    def simple_add(btn):          # drop the "&admin=..." part of the add-to-group link
        if btn.url and "&admin=" in btn.url:
            return B(btn.text, url=btn.url.split("&admin=")[0])
        return btn

    def no_urls(btn):
        return None if btn.url else btn

    return [ui, rebuild(simple_add), rebuild(no_urls)]


async def _send(message, text: str, ui):
    """Photo + caption when START_IMG works, plain text otherwise; then colour the buttons.
    Every failure is logged with the button links so a bad link is easy to spot."""
    urls = [b.url for row in ui[0].inline_keyboard for b in row if b.url]
    for n, (markup, styles, icons) in enumerate(_variants(ui)):
        kinds = (["photo"] if START_IMG else []) + ["text"]
        for kind in kinds:
            try:
                if kind == "photo":
                    sent = await message.reply_photo(START_IMG, caption=text, reply_markup=markup,
                                                     parse_mode=ParseMode.HTML)
                else:
                    sent = await message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML,
                                                    **NO_PREVIEW)
            except Exception as e:
                logging.warning(f"start {kind} failed (try {n + 1}): {type(e).__name__}: {e} | links={urls}")
                continue
            if markup:
                await colorize(sent, markup, styles, icons)
            return sent
    return None


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
                                          **NO_PREVIEW)
    except MessageNotModified:
        pass
    except Exception as e:
        logging.warning(f"help menu edit failed: {type(e).__name__}: {e}")
        return
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
        await prepare(client)
        await _notify_new_user(client, message.from_user)

        if len(message.command) > 1 and message.command[1] == "help":
            return await _send(message, _help_text(), _help_ui())
        await _send(message, _start_text(message.from_user), _start_ui(username))

    @app.on_message(filters.command("help"))
    async def help_cmd(client, message):
        await prepare(client)
        if message.chat.type != ChatType.PRIVATE:
            return await _send(message, S.START_GP.format(html.escape(BOT_NAME)),
                               _pm_button(client.me.username))
        await _send(message, _help_text(), _help_ui())

    _bg = set()

    @app.on_callback_query(filters.regex(r"^help:"))
    async def help_cb(client, query):
        # Answer the tap FIRST so the button stops "loading" at once, then build the page.
        try:
            await query.answer()
        except Exception:
            pass
        # Refreshing icons/links may hit the database - never make a tap wait for it.
        t = asyncio.create_task(prepare(client))
        _bg.add(t)
        t.add_done_callback(_bg.discard)

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
