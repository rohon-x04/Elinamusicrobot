# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - /start (one short message, nothing else)
# ============================================================
from pyrogram import Client, filters
from config import BOT_NAME


def register_start_handlers(app: Client):

    @app.on_message(filters.private & filters.command("start"))
    async def start_cmd(client, message):
        await message.reply_text(
            f"🎵 {BOT_NAME}\n\n"
            "Add me to your group, start a voice chat and use /play <song name or link>."
        )
