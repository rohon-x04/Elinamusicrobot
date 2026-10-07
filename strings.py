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
