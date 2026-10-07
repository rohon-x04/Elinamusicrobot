# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Shared helpers
# ============================================================

import time

from pyrogram.enums import ChatMemberStatus
from pyrogram.types import Message

ADMIN_STATUSES = (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)

# Short-lived cache of chat-member lookups (admin checks).
_MEMBER_CACHE: dict = {}
_MEMBER_TTL = 45


async def get_member(client, chat_id, user_id):
    """Cached get_chat_member. Returns None on any failure - never raises."""
    key = (chat_id, user_id)
    now = time.monotonic()
    hit = _MEMBER_CACHE.get(key)
    if hit and hit[0] > now:
        return hit[1]
    try:
        member = await client.get_chat_member(chat_id, user_id)
    except Exception:
        member = None
    if len(_MEMBER_CACHE) > 5000:
        _MEMBER_CACHE.clear()
    _MEMBER_CACHE[key] = (now + _MEMBER_TTL, member)
    return member


async def is_admin(client, chat_id, user_id) -> bool:
    member = await get_member(client, chat_id, user_id)
    return bool(member and member.status in ADMIN_STATUSES)


def is_anonymous_admin(message: Message) -> bool:
    """Admins posting as the group itself have no from_user."""
    return (
        message.from_user is None
        and message.sender_chat is not None
        and message.sender_chat.id == message.chat.id
    )


async def sender_is_admin(client, message: Message) -> bool:
    if is_anonymous_admin(message):
        return True
    if not message.from_user:
        return False
    return await is_admin(client, message.chat.id, message.from_user.id)


def mention(user) -> str:
    """Clickable name that works for users without a @username too."""
    name = (user.first_name or "User").replace("[", "(").replace("]", ")")
    return f"[{name}](tg://user?id={user.id})"
