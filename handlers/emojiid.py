# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - /emojiid  (owner & auth users)
# Gives you the ID of premium (custom) emoji so you can put them on the start buttons:
#   ICON_ADD / ICON_HELP / ICON_CLOSE   (strings.py or environment variables)
# Usage: send  /emojiid  together with the emoji, or reply to a message that has them.
# ============================================================
import html

from pyrogram import Client, filters
from pyrogram.enums import MessageEntityType, ParseMode

from config import is_owner
from handlers import icons

USAGE = (
    "<blockquote>🆔 <b>ᴇᴍᴏᴊɪ ɪᴅ</b>\n\n"
    "sᴇɴᴅ <code>/emojiid</code> ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ ᴇᴍᴏᴊɪ ɪɴ ᴛʜᴇ sᴀᴍᴇ ᴍᴇssᴀɢᴇ, ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛʜᴀᴛ ʜᴀs ᴛʜᴇᴍ.\n\n"
    "<b>ꜱᴇᴛ ᴛʜᴇ ꜱᴛᴀʀᴛ ʙᴜᴛᴛᴏɴ ɪᴄᴏɴꜱ:</b> <code>/emojiid set</code> + ᴛʜʀᴇᴇ ᴇᴍᴏᴊɪ ɪɴ ᴛʜɪꜱ ᴏʀᴅᴇʀ:\n"
    "1) <b>ʙᴀᴅɢᴇ</b> (ᴀᴅᴅ ᴍᴇ)  2) <b>ᴄʜᴇᴄᴋ</b> (ʜᴇʟᴘ)  3) <b>ᴛʀᴀꜱʜ</b> (ᴄʟᴏꜱᴇ)\n"
    "<code>/emojiid reset</code> — ʙᴀᴄᴋ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ.</blockquote>"
)


def _emojis(text, entities) -> list:
    """[(emoji_char, custom_emoji_id), ...] found in a message."""
    out = []
    if not text or not entities:
        return out
    raw = text.encode("utf-16-le")                    # Telegram offsets are UTF-16 units
    for e in entities:
        if e.type == MessageEntityType.CUSTOM_EMOJI:
            ch = raw[e.offset * 2:(e.offset + e.length) * 2].decode("utf-16-le", "ignore")
            out.append((ch, str(e.custom_emoji_id)))
    return out


def register_emojiid_handlers(app: Client):

    @app.on_message(filters.command("emojiid"))
    async def emojiid_cmd(client, message):
        if not (message.from_user and is_owner(message.from_user.id)):
            return

        args = [a.lower() for a in message.command[1:]]
        if "reset" in args:
            try:
                await icons.reset_icons()
                return await message.reply_text("<blockquote>♻️ ɪᴄᴏɴs ʀᴇsᴇᴛ.</blockquote>", parse_mode=ParseMode.HTML)
            except Exception as ex:
                return await message.reply_text(f"❌ {html.escape(str(ex))}")

        found = _emojis(message.text, message.entities)
        r = message.reply_to_message
        if r:
            found += _emojis(r.text or r.caption, r.entities or r.caption_entities)

        if not found:
            return await message.reply_text(USAGE, parse_mode=ParseMode.HTML)

        if "set" in args:
            if len(found) < 3:
                return await message.reply_text(USAGE, parse_mode=ParseMode.HTML)
            try:
                await icons.save_icons(found[0][1], found[1][1], found[2][1])
            except Exception as ex:
                return await message.reply_text(f"❌ {html.escape(str(ex))}")
            return await message.reply_text(
                "<blockquote>✅ <b>ɪᴄᴏɴs sᴀᴠᴇᴅ</b>\nsᴇɴᴅ /start ᴛᴏ sᴇᴇ ᴛʜᴇᴍ.\n"
                "<i>ᴛʜᴇʏ ᴏɴʟʏ sʜᴏᴡ ɪꜰ ᴛʜᴇ ʙᴏᴛ ᴏᴡɴᴇʀ ʜᴀs ᴛᴇʟᴇɢʀᴀᴍ ᴘʀᴇᴍɪᴜᴍ.</i></blockquote>",
                parse_mode=ParseMode.HTML)

        lines = [f"{i}. {html.escape(ch)}  <code>{eid}</code>" for i, (ch, eid) in enumerate(found, 1)]
        text = "<blockquote>🆔 <b>ᴄᴜsᴛᴏᴍ ᴇᴍᴏᴊɪ ɪᴅs</b>\n\n" + "\n".join(lines) + "</blockquote>"
        if len(found) >= 3:
            ids = [eid for _, eid in found[:3]]
            text += (
                "\n<blockquote>ᴘᴀsᴛᴇ ɪɴ ʏᴏᴜʀ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ:\n"
                f"<code>ICON_ADD={ids[0]}\nICON_HELP={ids[1]}\nICON_CLOSE={ids[2]}</code></blockquote>"
            )
        await message.reply_text(text, parse_mode=ParseMode.HTML)
