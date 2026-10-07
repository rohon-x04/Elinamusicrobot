# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music (voice-chat player)
# ============================================================
import asyncio
import traceback

from .player import music_player
from .handlers import register_music_handlers

__all__ = ["music_player", "register_music_handlers", "run_with_music"]


def run_with_music(app):
    """Drop-in replacement for app.run(): registers the music commands, starts
    the bot, starts the assistant + voice-call engine, then idles."""
    from pyrogram import idle

    register_music_handlers(app)

    async def _run():
        await app.start()
        try:
            await music_player.start(app)   # no-op if STRING_SESSION is blank
        except Exception as e:
            print("⚠️ Music system failed to start (bot keeps running):", e)
            traceback.print_exc()
        await idle()
        await music_player.stop()
        await app.stop()

    asyncio.get_event_loop().run_until_complete(_run())
