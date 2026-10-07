# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - EDITABLE TEXTS
# ------------------------------------------------------------
# Change any text here. HTML tags are allowed (<b>, <code>, <blockquote>).
# Keep the {0} {1} ... placeholders - they are filled in by the bot.
# ============================================================

# ---------------- Broadcast ----------------
GCAST_USAGE = (
    "<blockquote>📣  <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴜsᴀɢᴇ:</b>\n\n"
    "/broadcast [ʀᴇᴘʟʏ ᴛᴏ ᴍᴇssᴀɢᴇ]  ᴏʀ  /broadcast ʏᴏᴜʀ ᴛᴇxᴛ\n\n"
    "<b>ᴏᴘᴛɪᴏɴs:</b>\n"
    "▸  <code>-user</code>  — ᴀʟsᴏ sᴇɴᴅ ᴛᴏ ᴜsᴇʀs (ᴅᴍ)\n"
    "▸  <code>-nochat</code>  — sᴋɪᴘ ɢʀᴏᴜᴘs\n"
    "▸  <code>-copy</code>  — ɴᴏ ꜰᴏʀᴡᴀʀᴅ ᴛᴀɢ\n"
    "▸  <code>-pin</code>  — ᴘɪɴ ɪɴ ɢʀᴏᴜᴘs\n\n"
    "/stop_gcast — sᴛᴏᴘ ᴀ ʀᴜɴɴɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ</blockquote>"
)
GCAST_NOT_OWNER = "<blockquote>❌  ᴏɴʟʏ ᴛʜᴇ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.</blockquote>"
GCAST_ACTIVE = "<blockquote>⏳  ᴀ ʙʀᴏᴀᴅᴄᴀsᴛ ɪs ᴀʟʀᴇᴀᴅʏ ʀᴜɴɴɪɴɢ.</blockquote>"
GCAST_INACTIVE = "<blockquote>📣  ɴᴏ ʙʀᴏᴀᴅᴄᴀsᴛ ɪs ʀᴜɴɴɪɴɢ.</blockquote>"
GCAST_NO_TARGET = "<blockquote>⚠️  ɴᴏ ᴄʜᴀᴛs ᴛᴏ sᴇɴᴅ ᴛᴏ.</blockquote>"
GCAST_START = "<blockquote>📣  ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴀʀᴛᴇᴅ — {0} ᴄʜᴀᴛs ɪɴ ǫᴜᴇᴜᴇ.</blockquote>"
GCAST_STOP = "<blockquote>🛑  ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴏᴘ ʀᴇǫᴜᴇsᴛᴇᴅ.</blockquote>"
GCAST_END = (
    "<blockquote>✅  <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ</b>\n\n"
    "▸  ɢʀᴏᴜᴘs sᴇɴᴛ: <b>{0}</b>\n"
    "▸  ᴜsᴇʀs sᴇɴᴛ: <b>{1}</b>\n"
    "▸  ꜰᴀɪʟᴇᴅ: <b>{2}</b></blockquote>"
)
GCAST_STOPPED = (
    "<blockquote>🛑  <b>ʙʀᴏᴀᴅᴄᴀsᴛ sᴛᴏᴘᴘᴇᴅ</b>\n\n"
    "▸  ɢʀᴏᴜᴘs sᴇɴᴛ: <b>{0}</b>\n"
    "▸  ᴜsᴇʀs sᴇɴᴛ: <b>{1}</b>\n"
    "▸  ꜰᴀɪʟᴇᴅ: <b>{2}</b></blockquote>"
)
GCAST_LOG = (
    "<blockquote>📣  <b>ʙʀᴏᴀᴅᴄᴀsᴛ ʟᴏɢ</b>\n\n"
    "👤  <code>{0}</code>  ┊  {1}\n"
    "📋  ᴄᴏᴍᴍᴀɴᴅ: <code>{2}</code></blockquote>"
)

# ---------------- New / removed group log ----------------
NEW_CHAT_TITLE = "<blockquote>🟢 <b>ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ ᴀᴅᴅᴇᴅ ɪɴ ᴀ ɴᴇᴡ ɢʀᴏᴜᴘ</b></blockquote>"
LEFT_CHAT_TITLE = "<blockquote>🔴 <b>ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ᴀ ɢʀᴏᴜᴘ</b></blockquote>"

NEW_CHAT_BODY = (
    "<blockquote>\n"
    "🔖 <b>ᴄʜᴀᴛ ɴᴀᴍᴇ:</b> {name}\n"
    "🆔 <b>ᴄʜᴀᴛ ɪᴅ:</b> <code>{id}</code>\n"
    "👤 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {username}\n"
    "🔗 <b>ʟɪɴᴋ:</b> {link}\n"
    "👥 <b>ᴍᴇᴍʙᴇʀs:</b> {members}\n"
    "🤵 <b>ᴀᴅᴅᴇᴅ ʙʏ:</b> {by}\n"
    "</blockquote>"
)
LEFT_CHAT_BODY = (
    "<blockquote>\n"
    "🔖 <b>ᴄʜᴀᴛ ɴᴀᴍᴇ:</b> {name}\n"
    "🆔 <b>ᴄʜᴀᴛ ɪᴅ:</b> <code>{id}</code>\n"
    "👤 <b>ᴜsᴇʀɴᴀᴍᴇ:</b> {username}\n"
    "🔗 <b>ʟɪɴᴋ:</b> {link}\n"
    "🚫 <b>ʀᴇᴍᴏᴠᴇᴅ ʙʏ:</b> {by}\n"
    "</blockquote>"
)

PRIVATE_GROUP = "ᴘʀɪᴠᴀᴛᴇ ɢʀᴏᴜᴘ"
UNKNOWN = "ᴜɴᴋɴᴏᴡɴ"
NO_INVITE_PERM = "❌ ɴᴏ ɪɴᴠɪᴛᴇ ᴘᴇʀᴍɪssɪᴏɴ"
NOT_ADMIN = "❌ ʙᴏᴛ ɴᴏᴛ ᴀᴅᴍɪɴ"
LINK_FAILED = "❌ ᴜɴᴀʙʟᴇ ᴛᴏ ɢᴇᴛ ʟɪɴᴋ"

# ---------------- /link (owner) ----------------
LINK_USAGE = "⚠️ Usage:\n/link <group_id>"
LINK_OK = "🔗 <b>Group Link:</b>\n{0}"

# ---------------- /setstring  /delstring ----------------
STRING_NOT_OWNER = "<blockquote>❌  ᴏɴʟʏ ᴛʜᴇ ᴏᴡɴᴇʀ ᴄᴀɴ ᴜsᴇ ᴛʜɪs.</blockquote>"
STRING_USAGE = (
    "<blockquote>🎧  <b>ᴜsᴀɢᴇ:</b>\n\n"
    "/setstring <code>your_session_string</code>\n"
    "/delstring — ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ᴀssɪsᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ\n\n"
    "ᴜsᴇ ᴀ <b>sᴘᴀʀᴇ</b> ᴀᴄᴄᴏᴜɴᴛ. ᴛʜᴇ sᴇssɪᴏɴ ɪs ᴀ ᴘᴀssᴡᴏʀᴅ — ɴᴇᴠᴇʀ sʜᴀʀᴇ ɪᴛ.</blockquote>"
)
STRING_CHECKING = "<blockquote>⏳  ᴄʜᴇᴄᴋɪɴɢ sᴇssɪᴏɴ...</blockquote>"
STRING_OK = (
    "<blockquote>✅  <b>ᴀssɪsᴛᴀɴᴛ ᴀᴅᴅᴇᴅ</b>\n\n"
    "👤  {0}  ┊  <code>{1}</code>\n"
    "ᴍᴜsɪᴄ ɪs ʀᴇᴀᴅʏ — ɴᴏ ʀᴇsᴛᴀʀᴛ ɴᴇᴇᴅᴇᴅ.</blockquote>"
)
STRING_FAILED = "<blockquote>❌  <b>ꜰᴀɪʟᴇᴅ</b>\n<code>{0}</code></blockquote>"
STRING_REMOVED = (
    "<blockquote>🗑  ᴀssɪsᴛᴀɴᴛ ʀᴇᴍᴏᴠᴇᴅ. ᴍᴜsɪᴄ ɪs ᴏꜰꜰ ᴜɴᴛɪʟ ʏᴏᴜ ᴜsᴇ /setstring ᴀɢᴀɪɴ.\n"
    "<i>ɪꜰ <code>STRING_SESSION</code> ɪs sᴇᴛ ɪɴ ʏᴏᴜʀ ᴇɴᴠ, ɪᴛ ᴡɪʟʟ ʙᴇ ᴜsᴇᴅ ᴀɢᴀɪɴ ᴀꜰᴛᴇʀ ᴀ ʀᴇsᴛᴀʀᴛ.</i></blockquote>"
)
STRING_DELETE_MANUALLY = "\n\n⚠️ ɪ ᴄᴏᴜʟᴅɴ'ᴛ ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ᴍᴇssᴀɢᴇ — ᴅᴇʟᴇᴛᴇ ɪᴛ ʏᴏᴜʀsᴇʟꜰ."

# ============================================================
# 🏠 /start and /help  (edit freely)
# ============================================================
# Fill these links to show the buttons. Leave "" to hide a button.
SUPPORT_CHAT_URL = ""        # e.g. "https://t.me/yourgroup"
SUPPORT_CHANNEL_URL = ""     # e.g. "https://t.me/yourchannel"  (the "Updates" button)
OWNER_URL = ""               # e.g. "https://t.me/yourusername"

# ---- /start screen buttons ----
BTN_ADD = "ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ"
BTN_HELP = "「 ʜᴇʟᴘ ᴀɴᴅ ᴄᴏᴍᴍᴀɴᴅs 」"
BTN_SUPPORT = "「 sᴜᴘᴘᴏʀᴛ 」"
BTN_UPDATES = "「 ᴜᴘᴅᴀᴛᴇs 」"
BTN_OWNER = "「 ᴏᴡɴᴇʀ 」"
BTN_CLOSE = "🗑 ᴄʟᴏsᴇ"
BTN_BACK = "• ʙᴀᴄᴋ •"
BTN_OPEN_PM = "📖 ᴏᴘᴇɴ ʜᴇʟᴘ ɪɴ ᴘᴍ"

# {0} = user's first name, {1} = bot name
START_PM = (
    "<blockquote>☯ ʜᴇʟʟᴏ • <b>{0}</b> ɴɪᴄᴇ ᴛᴏ ᴍᴇᴇᴛ ʏᴏᴜ 🪐\n\n"
    "⚬⚬● ᴛʜɪs ɪs <b>{1}</b>\n\n"
    "🎶 ᴀ ᴘʀᴇᴍɪᴜᴍ ᴅᴇsɪɢɴᴇᴅ ᴍᴜsɪᴄ ᴘʟᴀʏᴇʀ ʙᴏᴛ ꜰᴏʀ ᴛᴇʟᴇɢʀᴀᴍ ɢʀᴏᴜᴘ & ᴄʜᴀɴɴᴇʟ.\n\n"
    "» ɪꜰ ᴀɴʏ ʜᴇʟᴘ ᴛᴀᴘ ᴛᴏ ʜᴇʟᴘ ʙᴜᴛᴛᴏɴ.\n\n"
    "•──  ‥  ──────────  ·❖·  ──────────  ‥  ──•</blockquote>"
)
# {0} = bot name
START_GP = (
    "<blockquote>🎵 <b>{0}</b> ɪs ᴀʟɪᴠᴇ!\n"
    "sᴛᴀʀᴛ ᴀ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ ᴀɴᴅ ᴜsᴇ <code>/play</code> ᴛᴏ ᴘʟᴀʏ ᴍᴜsɪᴄ.</blockquote>"
)

# ---- /help menu ----
# {0} = "support chat" (a link when SUPPORT_CHAT_URL is set)
HELP_MAIN = (
    "🔹 <b>ᴄʜᴏᴏsᴇ ᴄᴀᴛᴇɢᴏʀʏ ꜰᴏʀ ʏᴏᴜ ɢᴇᴛ ʜᴇʟᴘ</b>\n\n"
    "✈️ <b>ᴀsᴋ ʏᴏᴜʀ ᴅᴏᴜʙᴛs ᴀᴛ {0}</b>\n\n"
    "➤ <b>ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴄᴀɴ ʙᴇ ᴜsᴇᴅ ᴡɪᴛʜ : /</b>"
)
HELP_SUPPORT_TEXT = "sᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ"

# (key, button label, colour)   colour: success = green, primary = blue, danger = red
# 3 buttons per row. Add / remove / reorder freely - each key needs a page in HELP_PAGES.
HELP_CATEGORIES = [
    ("play",      "• ᴘʟᴀʏ •",         "success"),
    ("queue",     "ǫᴜᴇᴜᴇ",            "success"),
    ("loop",      "ʟᴏᴏᴘ",             "success"),
    ("autoplay",  "• ᴀᴜᴛᴏᴘʟᴀʏ •",     "success"),
    ("favs",      "ꜰᴀᴠs",             "success"),
    ("np",        "ɴᴏᴡ & ᴘɪɴɢ",       "success"),
    ("welcome",   "• ᴡᴇʟᴄᴏᴍᴇ •",      "success"),
    ("broadcast", "• ʙʀᴏᴀᴅᴄᴀsᴛ •",   "danger"),
    ("assistant", "• ᴀssɪsᴛᴀɴᴛ •",    "danger"),
]

# Each page = bold underlined title + one blockquote per group of commands.
HELP_PAGES = {
    "play": (
        "<b><u>ᴘʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs:</u></b>\n\n"
        "<blockquote>/play [name/link]: ᴘʟᴀʏ ᴀᴜᴅɪᴏ ɪɴ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.\n"
        "/vplay [name/link]: ᴘʟᴀʏ ᴠɪᴅᴇᴏ ɪɴ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ.</blockquote>\n"
        "<blockquote>/pause: ᴘᴀᴜsᴇ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ.\n"
        "/resume: ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴘᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ.\n"
        "/skip: sᴋɪᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ sᴛʀᴇᴀᴍ.\n"
        "/end: sᴛᴏᴘ ᴛʜᴇ sᴛʀᴇᴀᴍ ᴀɴᴅ ʟᴇᴀᴠᴇ.</blockquote>"
    ),
    "queue": (
        "<b><u>ǫᴜᴇᴜᴇ ᴄᴏᴍᴍᴀɴᴅs:</u></b>\n\n"
        "<blockquote>/queue: sʜᴏᴡs ᴛʜᴇ ᴄᴜʀʀᴇɴᴛʟʏ ǫᴜᴇᴜᴇᴅ ᴛʀᴀᴄᴋs.\n"
        "/skip: ᴊᴜᴍᴘ ᴛᴏ ᴛʜᴇ ɴᴇxᴛ ᴛʀᴀᴄᴋ ɪɴ ᴛʜᴇ ǫᴜᴇᴜᴇ.</blockquote>"
    ),
    "loop": (
        "<b><u>ʟᴏᴏᴘ ᴄᴏᴍᴍᴀɴᴅs:</u></b>\n\n"
        "<blockquote>/loop: ᴛᴏɢɢʟᴇ ʀᴇᴘᴇᴀᴛ ꜰᴏʀ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ.</blockquote>"
    ),
    "autoplay": (
        "<b><u>ᴀᴜᴛᴏᴘʟᴀʏ ᴄᴏᴍᴍᴀɴᴅs:</u></b>\n\n"
        "<blockquote>/autoplay: ᴋᴇᴇᴘ ᴘʟᴀʏɪɴɢ sɪᴍɪʟᴀʀ sᴏɴɢs ᴡʜᴇɴ ᴛʜᴇ ǫᴜᴇᴜᴇ ᴇɴᴅs.</blockquote>"
    ),
    "favs": (
        "<b><u>ꜰᴀᴠᴏᴜʀɪᴛᴇs ᴄᴏᴍᴍᴀɴᴅs:</u></b>\n\n"
        "<blockquote>ᴛᴀᴘ ❤️ ᴏɴ ᴛʜᴇ ᴘʟᴀʏᴇʀ ᴛᴏ sᴀᴠᴇ ᴀ sᴏɴɢ.</blockquote>\n"
        "<blockquote>/favs: sʜᴏᴡ ʏᴏᴜʀ sᴀᴠᴇᴅ sᴏɴɢs.\n"
        "/playfav: ᴘʟᴀʏ ʏᴏᴜʀ ꜰᴀᴠᴏᴜʀɪᴛᴇs.</blockquote>"
    ),
    "np": (
        "<b><u>ɴᴏᴡ ᴘʟᴀʏɪɴɢ & ᴘɪɴɢ ᴄᴏᴍᴍᴀɴᴅs:</u></b>\n\n"
        "<blockquote>/np: sʜᴏᴡ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ sᴏɴɢ ᴄᴀʀᴅ ᴡɪᴛʜ ᴘʀᴏɢʀᴇss.\n"
        "/ping: ᴄʜᴇᴄᴋ ʟᴀᴛᴇɴᴄʏ, ᴜᴘᴛɪᴍᴇ ᴀɴᴅ ᴍᴇᴍᴏʀʏ ᴜsᴀɢᴇ ᴏꜰ ᴛʜᴇ ʙᴏᴛ.\n"
        "/start: sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ.\n"
        "/help: sʜᴏᴡs ᴛʜᴇ ʜᴇʟᴘ ᴍᴇɴᴜ ᴏꜰ ᴛʜᴇ ʙᴏᴛ.</blockquote>"
    ),
    "welcome": (
        "<b><u>ᴡᴇʟᴄᴏᴍᴇ ᴄᴏᴍᴍᴀɴᴅs (ɢʀᴏᴜᴘ ᴀᴅᴍɪɴs):</u></b>\n\n"
        "<blockquote>/welcome [on/off]: ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪsᴀʙʟᴇ ᴛʜᴇ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ.\n"
        "/welcomecard [on/off]: ᴛᴏɢɢʟᴇ ᴛʜᴇ ᴡᴇʟᴄᴏᴍᴇ ɪᴍᴀɢᴇ.</blockquote>\n"
        "<blockquote>/setwelcome [text]: sᴇᴛ ᴀ ᴄᴜsᴛᴏᴍ ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ.\n"
        "/resetwelcome: ʙᴀᴄᴋ ᴛᴏ ᴛʜᴇ ᴅᴇꜰᴀᴜʟᴛ.</blockquote>"
    ),
    "broadcast": (
        "<b><u>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴍᴀɴᴅs (ᴏᴡɴᴇʀ ᴏɴʟʏ):</u></b>\n\n"
        "<blockquote>/broadcast [text or reply]: ʙʀᴏᴀᴅᴄᴀsᴛs ᴛʜᴇ ᴍᴇssᴀɢᴇ ᴛᴏ ᴀʟʟ ɢʀᴏᴜᴘs.\n"
        "  ▸ -user: ɪɴᴄʟᴜᴅᴇ ᴜsᴇʀs (ᴅᴍ).\n"
        "  ▸ -nochat: ᴇxᴄʟᴜᴅᴇs ɢʀᴏᴜᴘs.\n"
        "  ▸ -copy: ʀᴇᴍᴏᴠᴇs ꜰᴏʀᴡᴀʀᴅ ᴛᴀɢ.\n"
        "  ▸ -pin: ᴘɪɴs ɪɴ ɢʀᴏᴜᴘs.</blockquote>\n"
        "<blockquote>/stop_gcast: sᴛᴏᴘ ᴀ ʀᴜɴɴɪɴɢ ʙʀᴏᴀᴅᴄᴀsᴛ.</blockquote>"
    ),
    "assistant": (
        "<b><u>ᴀssɪsᴛᴀɴᴛ ᴄᴏᴍᴍᴀɴᴅs (ᴏᴡɴᴇʀ ᴏɴʟʏ, ɪɴ ᴅᴍ):</u></b>\n\n"
        "<blockquote>/setstring [session]: sᴇᴛ ᴛʜᴇ ᴀssɪsᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ.\n"
        "/delstring: ʀᴇᴍᴏᴠᴇ ᴛʜᴇ ᴀssɪsᴛᴀɴᴛ ᴀᴄᴄᴏᴜɴᴛ.</blockquote>\n"
        "<blockquote>/link [group_id]: ɢᴇᴛ ᴀ ɢʀᴏᴜᴘ ʟɪɴᴋ.</blockquote>"
    ),
}

# New-user notice sent to LOGGER_ID. {0}=name  {1}=id  {2}=username
NEW_USER_LOG = (
    "<blockquote>🟢 <b>ɴᴇᴡ ᴜsᴇʀ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ</b></blockquote>\n"
    "<blockquote>👤 {0}\n🆔 <code>{1}</code>\n🔖 {2}</blockquote>"
)

# ============================================================
# 🏓 /ping  (status card)
# ============================================================
# Image for the ping card (direct URL or file_id). "" = use START_IMG.
PING_IMG = ""

PING_WAIT = "<blockquote>ᴘɪɴɢɪɴɢ... ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</blockquote>"

# {bot} bot name   {icon} status icon   {status} status text   {latency} {uptime} {calls}
# {ram} {cpu} filled in by the bot.   {features} comes from PING_FEATURES below.
PING_CARD = (
    "<b>{bot}</b>, ᴀᴅᴠᴀɴᴄᴇᴅ ᴛᴇʟᴇɢʀᴀᴍ ᴍᴜsɪᴄ sᴛʀᴇᴀᴍɪɴɢ ʙᴏᴛ. "
    "ᴇxᴘᴇʀɪᴇɴᴄᴇ sᴛᴜᴅɪᴏ-ǫᴜᴀʟɪᴛʏ ᴀᴜᴅɪᴏ sᴛʀᴇᴀᴍɪɴɢ!\n\n"
    "<b>ʙᴏᴛ sᴛᴀᴛᴜs</b>\n\n"
    "<blockquote>{icon} <b>{status}</b>\n"
    "• ʟᴀᴛᴇɴᴄʏ: <code>{latency}ms</code>\n"
    "• ᴜᴘᴛɪᴍᴇ: <code>{uptime}</code>\n"
    "• ᴘʏᴛɢᴄᴀʟʟs: <code>{calls}ms</code>\n"
    "• ʀᴀᴍ: <code>{ram}</code>\n"
    "• ᴄᴘᴜ: <code>{cpu}%</code></blockquote>\n"
    "<blockquote>⚡ <b>ꜰᴇᴀᴛᴜʀᴇs</b>\n{features}</blockquote>\n"
    "<blockquote>{footer}</blockquote>"
)
PING_STATUS_OK = "ᴏɴʟɪɴᴇ & sᴛʀᴇᴀᴍɪɴɢ"
PING_STATUS_NO_ASSISTANT = "ᴏɴʟɪɴᴇ · ᴀssɪsᴛᴀɴᴛ ɴᴏᴛ sᴇᴛ"
PING_FEATURES = [
    "ᴄʀʏsᴛᴀʟ ᴄʟᴇᴀʀ ᴀᴜᴅɪᴏ",
    "sᴍᴀʀᴛ ǫᴜᴇᴜᴇ",
    "ᴀᴜᴛᴏᴘʟᴀʏ sɪᴍɪʟᴀʀ sᴏɴɢs",
    "ꜰᴀᴠᴏᴜʀɪᴛᴇs ʟɪʙʀᴀʀʏ",
    "ᴡᴇʟᴄᴏᴍᴇ ᴄᴀʀᴅs",
    "ʙʀᴏᴀᴅᴄᴀsᴛ ᴛᴏᴏʟs",
]
PING_FOOTER = "🚀 <b>ʀᴜɴɴɪɴɢ sᴍᴏᴏᴛʜʟʏ</b>"
