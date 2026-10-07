# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Remembers every user (DM) and group so /broadcast can reach them.
# Runs silently in its own handler group, never blocks other handlers.
# ============================================================
from pyrogram import Client, filters
import db


def register_tracker_handlers(app: Client):

    @app.on_message(filters.private & ~filters.service & ~filters.command("start"), group=-10)
    async def track_user(client, message):
        if message.from_user and not message.from_user.is_bot:
            await db.add_user(message.from_user.id)

    @app.on_message(filters.group, group=-10)
    async def track_group(client, message):
        await db.add_chat(message.chat.id)
