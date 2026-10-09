# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Handler registry
# To ADD a feature file: create handlers/<name>.py with a register_xxx(app) function,
# then import it here and call it in register_all_handlers.
# To REMOVE one: delete its import + call line below.
# ============================================================
from .tracker import register_tracker_handlers
from .start import register_start_handlers
from .welcome import register_welcome_handlers
from .new_chat import register_new_chat_handlers
from .broadcast import register_broadcast_handlers
from .string_session import register_string_handlers
from .ping import register_ping_handlers
from .emojiid import register_emojiid_handlers


def register_all_handlers(app):
    register_tracker_handlers(app)     # remembers users/groups for broadcast
    register_start_handlers(app)
    register_welcome_handlers(app)
    register_new_chat_handlers(app)    # group added/removed logs + /link
    register_broadcast_handlers(app)   # /broadcast, /stop_gcast
    register_ping_handlers(app)        # /ping status card
    register_emojiid_handlers(app)     # /emojiid (premium emoji ids for button icons)
    register_string_handlers(app)      # /setstring, /delstring (assistant account)
    print("✅ Handlers registered (tracker, start, welcome, new_chat, broadcast, string_session, ping, emojiid)")
