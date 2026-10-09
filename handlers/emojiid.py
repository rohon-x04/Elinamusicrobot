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

USAGE = (
    "<blockquote>🆔 <b>ᴇᴍᴏᴊɪ ɪᴅ</b>\n\n"
    "sᴇɴᴅ <code>/emojiid</code> ᴡɪᴛʜ ᴘʀᴇᴍɪᴜᴍ ᴇᴍᴏᴊɪ ɪɴ ᴛʜᴇ sᴀᴍᴇ ᴍᴇssᴀɢᴇ, ᴏʀ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛʜᴀᴛ ʜᴀs ᴛʜᴇᴍ.\n\n"
    "ꜰᴏʀ ᴛʜᴇ sᴛᴀʀᴛ ʙᴜᴛᴛᴏɴs sᴇɴᴅ ᴛʜᴇᴍ ɪɴ ᴛʜɪs ᴏʀᴅᴇʀ: "
    "<b>ʙᴀᴅɢᴇ</b> (ᴀᴅᴅ), <b>ᴄʜᴇᴄᴋ</b> (ʜᴇʟᴘ), <b>ᴛʀᴀsʜ</b> (ᴄʟᴏsᴇ).</blockquote>"
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

        found = _emojis(message.text, message.entities)
        r = message.reply_to_message
        if r:
            found += _emojis(r.text or r.caption, r.entities or r.caption_entities)

        if not found:
            return await message.reply_text(USAGE, parse_mode=ParseMode.HTML)

        lines = [f"{i}. {html.escape(ch)}  <code>{eid}</code>" for i, (ch, eid) in enumerate(found, 1)]
        text = "<blockquote>🆔 <b>ᴄᴜsᴛᴏᴍ ᴇᴍᴏᴊɪ ɪᴅs</b>\n\n" + "\n".join(lines) + "</blockquote>"
        if len(found) >= 3:
            ids = [eid for _, eid in found[:3]]
            text += (
                "\n<blockquote>ᴘᴀsᴛᴇ ɪɴ ʏᴏᴜʀ ᴇɴᴠɪʀᴏɴᴍᴇɴᴛ:\n"
                f"<code>ICON_ADD={ids[0]}\nICON_HELP={ids[1]}\nICON_CLOSE={ids[2]}</code></blockquote>"
            )
        await message.reply_text(text, parse_mode=ParseMode.HTML)
