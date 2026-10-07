# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Welcome messages
# ============================================================
#
# New members get the default welcome message + a welcome card picture
# (their profile photo, name, id and username - see welcome_card.py).
# Admins can swap the text with /setwelcome, and turn the picture off
# with /welcomecard off. If the card can't be made for any reason, the
# plain text welcome is sent instead - a welcome is never skipped.
#
# Two ways a join reaches us, and BOTH are handled:
#   - supergroups  -> ChatMemberUpdated event
#   - basic groups -> a "X joined" service message (no ChatMemberUpdated
#                     is sent there, so welcomes silently never worked)
# A de-dupe guard stops supergroups from welcoming twice.
# ============================================================

import asyncio
import html
import logging
import time
from pyrogram import Client, filters
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import Message, ChatMemberUpdated
import db
from .common import sender_is_admin, mention

try:
    from welcome_styles import generate_random_welcome as generate_welcome  # random card per member
except Exception:  # Pillow missing / font problem -> text-only welcomes
    generate_welcome = None
    logging.getLogger(__name__).warning(
        "welcome_card could not be imported - welcomes will be text only "
        "(add Pillow to requirements.txt).", exc_info=True
    )

logger = logging.getLogger(__name__)

# The default welcome message. {name} is a clickable mention; every value is
# HTML-escaped when it is filled in, so odd names can't break the message.
DEFAULT_WELCOME_HTML = (
    "🌸✨ ──────────────────── ✨🌸\n"
    "\n"
    "         🎊 ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴏᴜʀ ғᴀᴍɪʟʏ 🎊\n"
    "\n"
    "🌹 ɴᴀᴍᴇ ➤ {name}\n"
    "🌺 ᴜsᴇʀɴᴀᴍᴇ ➤ {username}\n"
    "🆔 ᴜsᴇʀ ɪᴅ ➤ {id}\n"
    "🏠 ɢʀᴏᴜᴘ ➤ {group}\n"
    "\n"
    "═════════════════════════"
)
# Used only if a custom /setwelcome text turns out to be broken.
FALLBACK_WELCOME = "👋 Welcome {first_name} to {title}!"

PLACEHOLDERS = "{first_name} {name} {mention} {username} {id} {title} {group}"
CAPTION_LIMIT = 1000          # Telegram allows 1024 characters in a photo caption

_recent_welcomes: dict = {}   # {(chat_id, user_id): monotonic time}
_DEDUP_SECONDS = 30


def _already_welcomed(chat_id: int, user_id: int) -> bool:
    now = time.monotonic()
    if len(_recent_welcomes) > 2000:
        for k in [k for k, t in _recent_welcomes.items() if now - t > _DEDUP_SECONDS]:
            _recent_welcomes.pop(k, None)
    last = _recent_welcomes.get((chat_id, user_id))
    _recent_welcomes[(chat_id, user_id)] = now
    return last is not None and (now - last) < _DEDUP_SECONDS


def _full_name(user) -> str:
    return " ".join(p for p in (user.first_name, getattr(user, "last_name", None)) if p) or "User"


def render_default_welcome(user, chat_title: str) -> str:
    """The default message, as HTML (send with ParseMode.HTML)."""
    return DEFAULT_WELCOME_HTML.format(
        name=f'<a href="tg://user?id={user.id}">{html.escape(_full_name(user))}</a>',
        username=f"@{html.escape(user.username)}" if user.username else "ɴᴏɴᴇ",
        id=user.id,
        group=html.escape(chat_title or "this group"),
    )


def _template_values(user, chat_title: str) -> dict:
    return dict(
        username=user.username or user.first_name,
        first_name=user.first_name,
        name=_full_name(user),
        mention=mention(user),
        id=user.id,
        title=chat_title or "this group",
        group=chat_title or "this group",
    )


def render_welcome(template: str, user, chat_title: str) -> str:
    """A custom /setwelcome text with its placeholders filled in."""
    try:
        return template.format(**_template_values(user, chat_title))
    except Exception:
        # unknown {placeholder}, stray "{" or "}" in the saved text, ...
        return FALLBACK_WELCOME.format(first_name=user.first_name, title=chat_title or "this group")


async def _fetch_avatar(client: Client, user):
    """The member's profile photo as in-memory bytes, or None (no photo / not
    visible / download failed - the card then shows an initial-letter circle)."""
    try:
        file_id = user.photo.big_file_id if getattr(user, "photo", None) else None
        if not file_id:
            async for p in client.get_chat_photos(user.id, limit=1):
                file_id = p.file_id
        if not file_id:
            return None
        return await asyncio.wait_for(client.download_media(file_id, in_memory=True), timeout=10)
    except Exception:
        logger.debug("No profile photo for %s", user.id, exc_info=True)
        return None


async def _make_card(client: Client, user):
    """The finished welcome card (PNG BytesIO), or None if it couldn't be made."""
    if generate_welcome is None:
        return None
    try:
        avatar = await _fetch_avatar(client, user)
        username = f"@{user.username}" if user.username else None
        # Pillow work is CPU-bound - run it off the event loop so the bot stays responsive.
        return await asyncio.to_thread(generate_welcome, avatar, _full_name(user), user.id, username)
    except Exception:
        logger.warning("Welcome card failed for %s", user.id, exc_info=True)
        return None


async def _send_welcome(client: Client, chat, user):
    if user.is_bot:
        return
    if not await db.get_welcome_status(chat.id):
        return
    if _already_welcomed(chat.id, user.id):
        return

    custom = await db.get_welcome_message(chat.id)
    if custom:
        text, extra = render_welcome(custom, user, chat.title), {}
    else:
        text, extra = render_default_welcome(user, chat.title), {"parse_mode": ParseMode.HTML}

    try:
        if await db.get_welcome_card(chat.id):
            card = await _make_card(client, user)
            if card is not None:
                try:
                    if len(text) <= CAPTION_LIMIT:
                        await client.send_photo(chat.id, card, caption=text, **extra)
                    else:  # too long for a caption: picture first, then the text
                        await client.send_photo(chat.id, card)
                        await client.send_message(chat.id, text, **extra)
                    return
                except Exception:
                    logger.warning("Couldn't send the welcome card, falling back to text", exc_info=True)
        await client.send_message(chat.id, text, **extra)
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")


def register_welcome_handlers(app: Client):

    @app.on_chat_member_updated()
    async def member_update(client: Client, cmu: ChatMemberUpdated):
        new = cmu.new_chat_member
        if not new or new.status != ChatMemberStatus.MEMBER:
            return
        # A real join: they weren't in the chat before. (Previously ANY old
        # state counted as "not a join" - so someone who was kicked with
        # /kick and rejoined never got welcomed.)
        old = cmu.old_chat_member
        if old is not None and old.status not in (ChatMemberStatus.LEFT, ChatMemberStatus.BANNED):
            return
        await _send_welcome(client, cmu.chat, new.user)

    @app.on_message(filters.group & filters.new_chat_members, group=1)
    async def member_joined_service(client: Client, message: Message):
        for user in message.new_chat_members or []:
            await _send_welcome(client, message.chat, user)

    @app.on_message(filters.group & filters.command("setwelcome"))
    async def set_welcome_cmd(client, message: Message):
        if not await sender_is_admin(client, message):
            return await message.reply_text("❌ You need to be an admin to use this.")

        parts = (message.text or "").split(None, 1)
        text = parts[1].strip() if len(parts) > 1 else ""
        if not text and message.reply_to_message:
            text = message.reply_to_message.text or message.reply_to_message.caption or ""
        if not text:
            return await message.reply_text(
                f"⚠️ Usage: /setwelcome your text\nPlaceholders: {PLACEHOLDERS}\n"
                "(/resetwelcome brings back the default message)"
            )
        if len(text) > 2000:
            return await message.reply_text("⚠️ Welcome messages can be at most 2000 characters.")

        # Catch a broken template now instead of silently falling back later.
        try:
            text.format(username="", first_name="", name="", mention="", id=0, title="", group="")
        except Exception:
            return await message.reply_text(
                f"❌ That text has a stray {{ or }} or an unknown placeholder.\nAllowed: {PLACEHOLDERS}"
            )

        await db.set_welcome_message(message.chat.id, text)
        await message.reply_text("✅ Welcome message updated.")

    @app.on_message(filters.group & filters.command("resetwelcome"))
    async def reset_welcome_cmd(client, message: Message):
        if not await sender_is_admin(client, message):
            return await message.reply_text("❌ You need to be an admin to use this.")
        await db.reset_welcome_message(message.chat.id)
        await message.reply_text("✅ Welcome message reset to the default.")

    @app.on_message(filters.group & filters.command("welcomecard"))
    async def welcomecard_cmd(client, message: Message):
        if len(message.command) < 2:
            on = await db.get_welcome_card(message.chat.id)
            return await message.reply_text(
                f"🖼️ The welcome card picture is {'ON' if on else 'OFF'}.\nUsage: /welcomecard on | off"
            )
        if not await sender_is_admin(client, message):
            return await message.reply_text("❌ You need to be an admin to use this.")
        arg = message.command[1].lower()
        if arg not in ("on", "off"):
            return await message.reply_text("⚠️ Usage: /welcomecard on | off")
        await db.set_welcome_card(message.chat.id, arg == "on")
        await message.reply_text(f"✅ Welcome card picture turned {'ON' if arg == 'on' else 'OFF'}.")

    @app.on_message(filters.group & filters.command("welcome"))
    async def welcome_toggle_cmd(client, message: Message):
        if len(message.command) < 2:
            enabled = await db.get_welcome_status(message.chat.id)
            card = await db.get_welcome_card(message.chat.id)
            custom = await db.get_welcome_message(message.chat.id)
            shown = custom if custom else "(the default welcome message)"
            return await message.reply_text(
                f"👋 Welcome messages are {'ON' if enabled else 'OFF'}, card picture {'ON' if card else 'OFF'}.\n\n"
                f"Current message:\n{shown}\n\n"
                "Usage: /welcome on | off   /welcomecard on | off   /setwelcome text   /resetwelcome",
                parse_mode=ParseMode.DISABLED,
            )

        if not await sender_is_admin(client, message):
            return await message.reply_text("❌ You need to be an admin to use this.")

        if message.command[1].lower() not in ("on", "off"):
            return await message.reply_text("⚠️ Usage: /welcome on | off")

        status = message.command[1].lower() == "on"
        await db.set_welcome_status(message.chat.id, status)
        await message.reply_text(f"✅ Welcome messages turned {'ON' if status else 'OFF'}.")
