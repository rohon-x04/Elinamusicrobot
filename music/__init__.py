# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Handler registry (welcome + start only; music lives in /music)
# ============================================================
from .start import register_start_handlers
from .welcome import register_welcome_handlers


def register_all_handlers(app):
    register_start_handlers(app)
    register_welcome_handlers(app)
    print("✅ Handlers registered (start, welcome)")
