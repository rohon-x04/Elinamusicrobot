# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: now-playing card text + inline buttons
# ============================================================
from html import escape

from pyrogram.types import InlineKeyboardButton as B, InlineKeyboardMarkup

from .youtube import fmt_time

# Same layout as the sample card. Colours (blue/green/red) are applied after
# sending by handlers.colorui.colorize(), which uses this nested style list.
STYLES = [
    ["primary"],                                   # progress bar row
    ["success", "primary", "primary", "primary", "danger"],
    ["primary", "primary", "primary"],
    ["success", "primary"],
    ["success"],
]


def _clock(sec: int, long: bool) -> str:
    sec = max(0, int(sec))
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if long else f"{m:02d}:{s:02d}"


def progress_text(pos: int, duration: int, width: int = 10) -> str:
    """e.g. '🎧 01:05 ———▣——————— 3:42'  (marker moves as the song plays)."""
    if not duration:
        return "🎧 LIVE"
    pos = max(0, min(int(pos), duration))
    i = round(width * pos / duration)
    bar = "—" * i + "▣" + "—" * (width - i)
    long = duration >= 3600
    return f"🎧 {_clock(pos, long)} {bar} {fmt_time(duration)}"


def controls(auto: bool, bot_username: str = "", pos: int = 0,
             duration: int = 0) -> InlineKeyboardMarkup:
    rows = [
        [B(progress_text(pos, duration), callback_data="mus:noop")],
        [B("▷", callback_data="mus:resume"), B("⏸", callback_data="mus:pause"),
         B("↻", callback_data="mus:replay"), B("⏭", callback_data="mus:skip"),
         B("▢", callback_data="mus:stop")],
        [B("< - 20ˢ", callback_data="mus:back"), B("🎵 ʀᴇᴄ", callback_data="mus:rec"),
         B("20ˢ + >", callback_data="mus:fwd")],
        [B("❤️ ꜰᴀᴠ", callback_data="mus:fav"),
         B("ᴀᴜᴛᴏ ✅" if auto else "ᴀᴜᴛᴏ", callback_data="mus:auto")],
    ]
    if bot_username:
        url = (f"https://t.me/{bot_username}?startgroup=true"
               "&admin=manage_video_chats+invite_users+delete_messages")
        rows.append([B("➕ ᴀᴅᴅ ᴍᴇ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ➕", url=url)])
    return InlineKeyboardMarkup(rows)


def card_text(track) -> str:
    title = track.title if len(track.title) <= 60 else track.title[:57] + "…"
    link = f'<a href="{escape(track.url)}">{escape(title)}</a>' if track.url else escape(title)
    t = "LIVE" if not track.duration else f"{fmt_time(track.duration)} ᴍɪɴᴜᴛᴇs"
    return (
        "➻ <b>sᴛᴀʀᴛᴇᴅ sᴛʀᴇᴀᴍɪɴɢ</b>\n\n"
        f"🔮 <b>ᴛɪᴛʟᴇ :</b> {link}\n"
        f"⏱ <b>ᴛɪᴍᴇ :</b> {t}\n"
        f"🪽 <b>ʙʏ :</b> {escape(track.requested_by)}\n\n"
        "🧸 <i>𝐏σᴡ𝛜ʀ𝛜𝛅 𝐁ʏ "
        '<a href="https://t.me/apex2network">˹ ꞋꞋꞌꞋ𝚨ᴘє𝙭 ɴᴇᴛᴡᴏʀᴋ˼</a></i>'
    )


# ---------------- "added to queue" card ----------------
# Same look as the sample screenshot: underlined heading quote, then a quote with
# TITLE / DURATION / REQUESTED BY, and the buttons  ▷  II  >>  ▣  +  DELETE.
QUEUED_STYLES = [["success", "primary", "primary", "danger"], ["danger"]]
QUEUED_TITLE_MAX = 25      # long titles are cut to this many characters (like the sample)


def _who(track) -> str:
    """Requester as a clickable (blue) name when we know their id."""
    name = escape(track.requested_by)
    uid = getattr(track, "requested_by_id", 0)
    return f'<a href="tg://user?id={uid}">{name}</a>' if uid else name


def queued_text(track, pos: int) -> str:
    title = track.title[:QUEUED_TITLE_MAX].rstrip()
    link = f'<a href="{escape(track.url)}">{escape(title)}</a>' if track.url else escape(title)
    dur = f"{_clock(track.duration, track.duration >= 3600)} ᴍɪɴ" if track.duration else "LIVE"
    return (
        f"<blockquote><u><b>ᴀᴅᴅᴇᴅ ᴛᴏ ǫᴜᴇᴜᴇ:</b> {pos} </u></blockquote>\n\n"
        f"<blockquote><b>ᴛɪᴛʟᴇ:</b> {link}\n"
        f"<b>ᴅᴜʀᴀᴛɪᴏɴ:</b> {dur}\n"
        f"<b>ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:</b> {_who(track)}</blockquote>"
    )


def queued_markup() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [B("▷", callback_data="mus:resume"), B("II", callback_data="mus:pause"),
         B(">>", callback_data="mus:skip"), B("▣", callback_data="mus:stop")],
        [B("DELETE", callback_data="mus:del")],
    ])


# ---------------- "similar songs" picker (Rec button / after the queue ends) ----------------
PICK_PER_PAGE = 4


def picker_pages(n: int) -> int:
    return max(1, -(-n // PICK_PER_PAGE))


def picker_markup(tracks, page: int = 0) -> InlineKeyboardMarkup:
    pages = picker_pages(len(tracks))
    page %= pages
    start = page * PICK_PER_PAGE
    rows = []
    for i, t in enumerate(tracks[start:start + PICK_PER_PAGE], start):
        title = t.title if len(t.title) <= 34 else t.title[:33] + "…"
        rows.append([B(f"🎵 {title} · {fmt_time(t.duration)}", callback_data=f"mus:pk:{i}")])
    nav = [B(f"{page + 1}/{pages}", callback_data="mus:noop")]
    if pages > 1:
        nav.append(B("More ›", callback_data="mus:pkn"))
    rows.append(nav)
    rows.append([B("🗑 Close", callback_data="mus:pkx")])
    return InlineKeyboardMarkup(rows)


def picker_styles(tracks, page: int = 0) -> list:
    pages = picker_pages(len(tracks))
    n = len(tracks[(page % pages) * PICK_PER_PAGE:(page % pages) * PICK_PER_PAGE + PICK_PER_PAGE])
    rows = [["success" if i == 0 else "primary"] for i in range(n)]
    rows.append(["success", "primary"] if pages > 1 else ["success"])
    rows.append(["danger"])
    return rows
