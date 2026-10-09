# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - /setstring and /delstring  (owner only, bot's DM only)
#
#   /setstring <session string>   ADD an assistant account (multi-assistants, no restart needed)
#   /assistants                   list the assistants and how busy each one is
#   /delstring [number]           remove assistant #number, or all of them
# Texts live in strings.py - edit them there.
# ============================================================
import html
import logging

from pyrogram import Client, filters
from pyrogram.enums import ParseMode

import strings as S
from config import is_owner


def register_string_handlers(app: Client):
    from music import music_player

    def _is_owner(message) -> bool:
        return bool(message.from_user and is_owner(message.from_user.id))

    @app.on_message(filters.command("setstring") & filters.private)
    async def set_string(client, message):
        if not _is_owner(message):
            return await message.reply_text(S.STRING_NOT_OWNER, parse_mode=ParseMode.HTML)
        if len(message.command) < 2:
            return await message.reply_text(S.STRING_USAGE, parse_mode=ParseMode.HTML)

        session = message.text.split(None, 1)[1].strip().strip("\"'`")

        # the session string is a password - remove it from the chat right away
        deleted = True
        try:
            await message.delete()
        except Exception:
            deleted = False

        note = await client.send_message(message.chat.id, S.STRING_CHECKING, parse_mode=ParseMode.HTML)
        err = await music_player.set_session(session)
        if err:
            logging.warning(f"/setstring failed: {err}")
            text = S.STRING_FAILED.format(html.escape(err))
        else:
            me = music_player.last_added.me
            text = S.STRING_OK.format(html.escape(me.first_name or "Assistant"), me.id)
            text += S.STRING_COUNT.format(len(music_player.assistants))
        if not deleted:
            text += S.STRING_DELETE_MANUALLY
        await note.edit_text(text, parse_mode=ParseMode.HTML)

    @app.on_message(filters.command("delstring") & filters.private)
    async def del_string(client, message):
        if not _is_owner(message):
            return await message.reply_text(S.STRING_NOT_OWNER, parse_mode=ParseMode.HTML)
        number = None
        if len(message.command) > 1:
            if not message.command[1].isdigit():
                return await message.reply_text(S.STRING_USAGE, parse_mode=ParseMode.HTML)
            number = int(message.command[1])
        try:
            err = await music_player.remove_session(number)
        except Exception as e:
            return await message.reply_text(S.STRING_FAILED.format(html.escape(str(e))),
                                            parse_mode=ParseMode.HTML)
        if err:
            return await message.reply_text(S.STRING_FAILED.format(html.escape(err)),
                                            parse_mode=ParseMode.HTML)
        await message.reply_text(S.STRING_REMOVED_ONE.format(number) if number else S.STRING_REMOVED,
                                 parse_mode=ParseMode.HTML)

    @app.on_message(filters.command("assistants") & filters.private)
    async def list_assistants(client, message):
        if not _is_owner(message):
            return await message.reply_text(S.STRING_NOT_OWNER, parse_mode=ParseMode.HTML)
        if not music_player.assistants:
            return await message.reply_text(S.ASSISTANTS_NONE, parse_mode=ParseMode.HTML)
        lines = []
        for i, a in enumerate(music_player.assistants, 1):
            me = a.me
            lines.append(f"<b>{i}.</b> {html.escape(me.first_name or 'Assistant')} "
                         f"<code>{me.id}</code>  ┊  {len(a.chats)} ᴀᴄᴛɪᴠᴇ ᴄʜᴀᴛ(s)")
        await message.reply_text(S.ASSISTANTS_LIST.format("\n".join(lines)), parse_mode=ParseMode.HTML)
