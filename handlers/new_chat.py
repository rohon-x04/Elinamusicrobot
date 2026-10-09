# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - New group / removed group notices + /link (owner)
# Texts live in strings.py - edit them there.
# ============================================================
import html
import logging

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import ChatAdminRequired, ChannelPrivate

import db
import strings as S
from handlers.common import NO_PREVIEW
from config import LOGGER_ID, START_IMG, is_owner


def _user_link(user) -> str:
    if not user:
        return S.UNKNOWN
    name = html.escape(user.first_name or "User")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


async def _chat_link(client, chat) -> str:
    try:
        if chat.username:
            return f"https://t.me/{chat.username}"
        me = await client.get_chat_member(chat.id, client.me.id)
        if me.privileges and me.privileges.can_invite_users:
            return await client.export_chat_invite_link(chat.id)
        return S.NO_INVITE_PERM
    except ChatAdminRequired:
        return S.NOT_ADMIN
    except Exception:
        return S.LINK_FAILED


async def _send_log(client, text: str):
    if not LOGGER_ID:
        return
    try:
        if START_IMG:
            await client.send_photo(LOGGER_ID, START_IMG, caption=text, parse_mode=ParseMode.HTML)
        else:
            await client.send_message(LOGGER_ID, text, parse_mode=ParseMode.HTML,
                                      **NO_PREVIEW)
    except Exception as e:
        logging.warning(f"logger send failed: {e}")


def register_new_chat_handlers(app: Client):

    # 🟢 Bot added to a group
    @app.on_message(filters.new_chat_members & filters.group)
    async def bot_added(client, message):
        if not any(m.id == client.me.id for m in message.new_chat_members):
            return
        chat = message.chat
        await db.add_chat(chat.id)

        try:
            members = await client.get_chat_members_count(chat.id)
        except Exception:
            members = S.UNKNOWN

        body = S.NEW_CHAT_BODY.format(
            name=html.escape(chat.title or ""),
            id=chat.id,
            username=f"@{chat.username}" if chat.username else S.PRIVATE_GROUP,
            link=await _chat_link(client, chat),
            members=members,
            by=_user_link(message.from_user),
        )
        await _send_log(client, f"{S.NEW_CHAT_TITLE}\n\n{body}")

    # 🔴 Bot removed from a group
    @app.on_message(filters.left_chat_member & filters.group)
    async def bot_removed(client, message):
        if message.left_chat_member.id != client.me.id:
            return
        chat = message.chat
        await db.remove_chat(chat.id)

        body = S.LEFT_CHAT_BODY.format(
            name=html.escape(chat.title or ""),
            id=chat.id,
            username=f"@{chat.username}" if chat.username else S.PRIVATE_GROUP,
            link=f"https://t.me/{chat.username}" if chat.username else S.PRIVATE_GROUP,
            by=_user_link(message.from_user),
        )
        await _send_log(client, f"{S.LEFT_CHAT_TITLE}\n\n{body}")

    # 🔗 /link <group_id>  (owner, private chat)
    @app.on_message(filters.command("link") & filters.private)
    async def get_group_link(client, message):
        if not message.from_user or not is_owner(message.from_user.id):
            return await message.reply_text("❌ You are not authorized.")
        if len(message.command) < 2:
            return await message.reply_text(S.LINK_USAGE)
        try:
            chat_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid group ID")
        try:
            chat = await client.get_chat(chat_id)
            link = await _chat_link(client, chat)
            await message.reply_text(S.LINK_OK.format(link), parse_mode=ParseMode.HTML,
                                     **NO_PREVIEW)
        except ChannelPrivate:
            await message.reply_text("❌ Bot is not in that group")
        except Exception as e:
            await message.reply_text(f"❌ Error:\n{e}")
