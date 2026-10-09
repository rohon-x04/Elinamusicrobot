# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: commands
# ============================================================
# /play /vplay /playnext /radio /pause /resume /skip /end /queue /shuffle /remove /clear
# /loop /np /autoplay(/autoqueue) /seek /volume /mute /unmute /favs /playfav
# admin controls: /auth /unauth /authusers /playmode /skipmode
# + the inline buttons under the now-playing card (callbacks 'mus:*')
#

import asyncio
import copy
import os
from html import escape

from pyrogram import Client, filters, enums
from pyrogram.types import Message

from handlers.colorui import colorize, edit_styled

from config import is_owner
from .settings import (MUSIC_DURATION_LIMIT, MUSIC_QUEUE_LIMIT, MUSIC_SUGGEST_AFTER_END,
                       MUSIC_DIRECT_STREAM)
from handlers.common import is_admin, is_anonymous_admin, NO_PREVIEW
from .player import music_player
from .youtube import search_track, prefetch, fmt_time, StreamError, Track
from .thumbnail import make_thumb
from .ui import (controls, STYLES, picker_markup, picker_styles, picker_pages,
                 queued_text, queued_markup, QUEUED_STYLES,
                 radio_markup, radio_styles, queue_markup, queue_styles, QUEUE_PAGE)
from .favs import get_favs, add_fav
from . import radio, chatcfg, cache

HTML = enums.ParseMode.HTML


async def _may_control(client, chat_id: int, user_id: int) -> bool:
    """Admin, bot owner, or an authorised user (/auth) of this group."""
    if is_owner(user_id):
        return True
    if user_id in (await chatcfg.get(chat_id)).auth:
        return True
    return await is_admin(client, chat_id, user_id)


async def _can_control(client, message: Message) -> bool:
    if is_anonymous_admin(message):
        return True
    user = message.from_user
    if not user:
        return False
    return await _may_control(client, message.chat.id, user.id)


async def _only_admins(client, message: Message) -> bool:
    """True for real admins / owner only (authorised users can't manage the auth list)."""
    if is_anonymous_admin(message):
        return True
    user = message.from_user
    if not user:
        return False
    return is_owner(user.id) or await is_admin(client, message.chat.id, user.id)


async def _can_play_id(client, chat_id: int, user_id: int) -> bool:
    cfg = await chatcfg.get(chat_id)
    return cfg.playmode == "all" or await _may_control(client, chat_id, user_id)


async def _can_play(client, message: Message) -> bool:
    cfg = await chatcfg.get(message.chat.id)
    return cfg.playmode == "all" or await _can_control(client, message)


NO_ADMIN = "❌ Only admins and authorised users can use this."


def register_music_handlers(app: Client):

    async def _show_queued(track, pos, status=None, chat_id=None):
        """'Added to queue' card with ▷ ⏸ >> ▢ and DELETE buttons."""
        text, markup = queued_text(track, pos), queued_markup()
        if status is not None:
            if await edit_styled(status, text, markup, QUEUED_STYLES, parse_mode="HTML"):
                return                      # edited + coloured in one call
            sent = await status.edit_text(text, reply_markup=markup, parse_mode=HTML,
                                          **NO_PREVIEW)
        else:
            sent = await app.send_message(chat_id, text, reply_markup=markup, parse_mode=HTML,
                                          **NO_PREVIEW)
        await colorize(sent, markup, QUEUED_STYLES)

    async def _drop_thumb(track):
        """Delete a pre-drawn thumbnail that ended up unused."""
        task, track.thumb_task = track.thumb_task, None
        if task:
            try:
                path = await task
                if path:
                    os.remove(path)
            except Exception:
                pass

    async def _play(client: Client, message: Message, video: bool, query_override: str = "",
                    front: bool = False):
        if not music_player.enabled:
            return await message.reply_text("🎵 The music system isn't enabled on this bot.")
        if front and not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        if not await _can_play(client, message):
            return await message.reply_text(
                "❌ Only admins can add songs in this group right now (admins: /playmode all).")

        query = query_override or (
            message.text.split(None, 1)[1].strip() if len(message.command) > 1 else "")
        if not query and message.reply_to_message:
            r = message.reply_to_message
            query = (r.text or r.caption or "").strip()
        if not query:
            return await message.reply_text(
                "⚠️ Usage: /play <song name or YouTube link>\n/vplay for video, /radio for live radio.")

        cid = message.chat.id
        user = message.from_user.first_name if message.from_user else "Anonymous"
        status = await message.reply_text("🔎 Searching...")

        # Search and "get the assistant into the group" run AT THE SAME TIME.
        join_task = asyncio.create_task(music_player.ensure_assistant(cid))
        try:
            track = await search_track(query, video, user)
            track.requested_by_id = message.from_user.id if message.from_user else 0
        except Exception:
            join_task.cancel()
            return await status.edit_text("❌ Couldn't find or load that. Try another name or link.")

        if not track.duration:
            join_task.cancel()
            return await status.edit_text("❌ That's a live stream - use /radio for live radio.")

        if MUSIC_DURATION_LIMIT and track.duration and track.duration > MUSIC_DURATION_LIMIT * 60:
            join_task.cancel()
            return await status.edit_text(
                f"❌ Too long. The limit is {MUSIC_DURATION_LIMIT} minutes.")

        st = music_player.state.get(cid)
        if st and len(st.queue) >= MUSIC_QUEUE_LIMIT:
            join_task.cancel()
            return await status.edit_text(f"❌ The queue is full ({MUSIC_QUEUE_LIMIT} tracks).")

        # Draw the thumbnail NOW (audio streams live, so no download is needed first).
        if not (st and st.current):
            if video or not MUSIC_DIRECT_STREAM:
                prefetch(track)
            track.thumb_task = asyncio.create_task(make_thumb(track))

        err = await join_task
        if err:
            await _drop_thumb(track)
            return await status.edit_text(f"❌ {err}")

        try:
            result, pos = await music_player.play_or_queue(cid, track, front=front)
        except Exception as e:
            music_player.state.pop(cid, None)
            music_player._unbind(cid)
            await _drop_thumb(track)
            hint = "" if isinstance(e, StreamError) else (
                "\n\nStart a voice chat in this group first, or make the assistant "
                "account an admin with 'Manage voice chats'.")
            return await status.edit_text(f"❌ Couldn't start playback: {escape(str(e))}{hint}",
                                          parse_mode=HTML)

        if result == "playing":
            try:
                await status.delete()
            except Exception:
                pass
            await music_player.announce(cid, track)   # thumbnail card + buttons
        elif result == "duplicate":
            await _drop_thumb(track)
            await status.edit_text("♻️ That song is already " + (
                "playing." if pos == 0 else f"in the queue (position {pos})."))
        else:
            await _drop_thumb(track)
            await _show_queued(track, pos, status=status)

    @app.on_message(filters.group & filters.command(["play", "p"]))
    async def play_cmd(client, message: Message):
        await _play(client, message, video=False)

    @app.on_message(filters.group & filters.command(["vplay", "vp"]))
    async def vplay_cmd(client, message: Message):
        await _play(client, message, video=True)

    @app.on_message(filters.group & filters.command("pause"))
    async def pause_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        try:
            ok = await music_player.pause(message.chat.id)
        except Exception:
            ok = False
        await message.reply_text("⏸ Paused." if ok else "⚠️ Nothing is playing (or it's already paused).")

    @app.on_message(filters.group & filters.command("resume"))
    async def resume_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        try:
            ok = await music_player.resume(message.chat.id)
        except Exception:
            ok = False
        await message.reply_text("▶️ Resumed." if ok else "⚠️ Nothing is paused.")

    @app.on_message(filters.group & filters.command(["skip", "next"]))
    async def skip_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if (await chatcfg.get(message.chat.id)).skipmode != "all" and not await _can_control(client, message):
            return await message.reply_text("❌ Only admins and authorised users can skip (/skipmode all opens it).")
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("⚠️ Nothing is playing.")
        await music_player.advance(message.chat.id, announce=True, skip=True)

    @app.on_message(filters.group & filters.command(["end", "stopmusic"]))
    async def end_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        ok = await music_player.end(message.chat.id)
        await message.reply_text("⏹ Stopped and cleared the queue." if ok else "⚠️ Nothing is playing.")

    @app.on_message(filters.group & filters.command("loop"))
    async def loop_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("⚠️ Nothing is playing.")
        st.loop = not st.loop
        await message.reply_text("🔁 Loop on - current track repeats." if st.loop else "➡️ Loop off.")

    def _queue_text(chat_id: int, st, page: int) -> str:
        cur = st.current
        lines = [f"▶️ <b>{escape(cur.title)}</b> [{fmt_time(cur.duration)}]"
                 + (f" · 👤 {escape(cur.requested_by)}" if cur.requested_by else "")]
        start = page * QUEUE_PAGE
        for i, t in enumerate(st.queue[start:start + QUEUE_PAGE], start + 1):
            who = " ♾" if t.requested_by == "Auto Queue" else ""
            lines.append(f"{i}. {escape(t.title[:60])} [{fmt_time(t.duration)}]{who}")
        flags = (" · 🔁 loop" if st.loop else "") + (" · ♾ auto queue" if music_player.is_auto(chat_id) else "")
        return (f"🎶 <b>Queue</b> — {len(st.queue)} waiting{flags}\n\n" + "\n".join(lines))

    @app.on_message(filters.group & filters.command(["queue", "q"]))
    async def queue_cmd(client, message: Message):
        if not music_player.enabled:
            return
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("📭 The queue is empty.")
        try:
            page = int(message.command[1]) - 1 if len(message.command) > 1 else 0
        except ValueError:
            page = 0
        pages = max(1, -(-len(st.queue) // QUEUE_PAGE))
        page = max(0, min(page, pages - 1))
        markup = queue_markup(len(st.queue), page) if len(st.queue) > QUEUE_PAGE else None
        sent = await message.reply_text(_queue_text(message.chat.id, st, page), parse_mode=HTML, reply_markup=markup,
                                        **NO_PREVIEW)
        if markup:
            await colorize(sent, markup, queue_styles(len(st.queue), page))

    # ---------------- smart queue + admin controls ----------------
    @app.on_message(filters.group & filters.command("playnext"))
    async def playnext_cmd(client, message: Message):
        await _play(client, message, video=False, front=True)

    @app.on_message(filters.group & filters.command("shuffle"))
    async def shuffle_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        n = await music_player.shuffle(message.chat.id)
        await message.reply_text(f"🔀 Shuffled {n} queued songs." if n else "⚠️ Need at least 2 songs in the queue.")

    @app.on_message(filters.group & filters.command(["remove", "rm"]))
    async def remove_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        try:
            n = int(message.command[1])
        except (IndexError, ValueError):
            return await message.reply_text("⚠️ Usage: /remove <queue number>  (see /queue)")
        t = await music_player.remove(message.chat.id, n)
        await message.reply_text(f"🗑 Removed <b>{escape(t.title[:60])}</b>." if t
                                 else "⚠️ No song with that number.", parse_mode=HTML)

    @app.on_message(filters.group & filters.command(["clear", "clearqueue"]))
    async def clear_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        n = await music_player.clear_queue(message.chat.id)
        await message.reply_text(f"🧹 Cleared {n} songs from the queue." if n else "📭 The queue is already empty.")

    @app.on_message(filters.group & filters.command(["volume", "vol"]))
    async def volume_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("⚠️ Nothing is playing.")
        if len(message.command) < 2:
            return await message.reply_text(f"🔊 Volume is <b>{st.volume}%</b>. Use /volume 1-200.",
                                            parse_mode=HTML)
        try:
            v = int(message.command[1].strip("%"))
        except ValueError:
            return await message.reply_text("⚠️ Usage: /volume <1-200>")
        if not 1 <= v <= 200:
            return await message.reply_text("⚠️ Volume must be between 1 and 200.")
        try:
            await music_player.set_volume(message.chat.id, v)
        except Exception as e:
            return await message.reply_text(f"❌ Couldn't change the volume: {escape(str(e)[:120])}")
        await message.reply_text(f"🔊 Volume set to <b>{v}%</b>.", parse_mode=HTML)

    @app.on_message(filters.group & filters.command(["mute", "unmute"]))
    async def mute_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        want = message.command[0].lower().split("@")[0] == "mute"
        try:
            ok = await music_player.set_mute(message.chat.id, want)
        except Exception as e:
            return await message.reply_text(f"❌ {escape(str(e)[:120])}")
        await message.reply_text(("🔇 Muted." if want else "🔊 Unmuted.") if ok
                                 else ("⚠️ Nothing is playing (or it's already " + ("muted)." if want else "unmuted).")))

    @app.on_message(filters.group & filters.command("seek"))
    async def seek_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        arg = message.command[1] if len(message.command) > 1 else ""
        usage = "⚠️ Usage: /seek 90  ·  /seek 1:30  ·  /seek +20  ·  /seek -15"
        if not arg:
            return await message.reply_text(usage)
        rel = arg[0] in "+-"
        try:
            parts = [int(x) for x in arg.lstrip("+-").split(":")]
            secs = sum(x * 60 ** i for i, x in enumerate(reversed(parts)))
        except ValueError:
            return await message.reply_text(usage)
        if arg.startswith("-"):
            secs = -secs
        pos = await music_player.seek(message.chat.id, **({"delta": secs} if rel else {"to": secs}))
        if pos is None:
            return await message.reply_text("⚠️ Nothing is playing.")
        if pos == -1:
            return await message.reply_text("⚠️ Can't seek a live stream.")
        await message.reply_text(f"⏩ Jumped to <b>{fmt_time(pos)}</b>.", parse_mode=HTML)
        await music_player.refresh_card(message.chat.id)

    @app.on_message(filters.group & filters.command("playmode"))
    async def playmode_cmd(client, message: Message):
        if not await _only_admins(client, message):
            return await message.reply_text("❌ Only admins can use this.")
        cid, arg = message.chat.id, (message.command[1].lower() if len(message.command) > 1 else "")
        if arg in ("all", "admins"):
            await chatcfg.set_mode(cid, "playmode", arg)
        mode = (await chatcfg.get(cid)).playmode
        await message.reply_text(
            f"🎛 Play mode: <b>{'everyone' if mode == 'all' else 'admins & authorised users only'}</b>\n"
            "Change it with /playmode all  or  /playmode admins", parse_mode=HTML)

    @app.on_message(filters.group & filters.command("skipmode"))
    async def skipmode_cmd(client, message: Message):
        if not await _only_admins(client, message):
            return await message.reply_text("❌ Only admins can use this.")
        cid, arg = message.chat.id, (message.command[1].lower() if len(message.command) > 1 else "")
        if arg in ("all", "admins"):
            await chatcfg.set_mode(cid, "skipmode", arg)
        mode = (await chatcfg.get(cid)).skipmode
        await message.reply_text(
            f"⏭ Skip mode: <b>{'everyone' if mode == 'all' else 'admins & authorised users only'}</b>\n"
            "Change it with /skipmode all  or  /skipmode admins", parse_mode=HTML)

    async def _target_user(client, message: Message):
        """User from a reply, a numeric id or a @username."""
        if message.reply_to_message and message.reply_to_message.from_user:
            return message.reply_to_message.from_user
        if len(message.command) > 1:
            ref = message.command[1].lstrip("@")
            try:
                return await client.get_users(int(ref) if ref.lstrip("-").isdigit() else ref)
            except Exception:
                return None
        return None

    @app.on_message(filters.group & filters.command(["auth", "unauth"]))
    async def auth_cmd(client, message: Message):
        if not await _only_admins(client, message):
            return await message.reply_text("❌ Only admins can use this.")
        on = message.command[0].lower().split("@")[0] == "auth"
        user = await _target_user(client, message)
        if not user:
            return await message.reply_text(
                f"⚠️ Reply to a user, or use /{'auth' if on else 'unauth'} <user id or @username>.")
        await chatcfg.set_auth(message.chat.id, user.id, on)
        name = f'<a href="tg://user?id={user.id}">{escape(user.first_name or "User")}</a>'
        await message.reply_text(
            f"✅ {name} can now control the music (skip, pause, queue, volume...)." if on
            else f"🗑 {name} is no longer an authorised user.", parse_mode=HTML)

    @app.on_message(filters.group & filters.command("authusers"))
    async def authusers_cmd(client, message: Message):
        cfg = await chatcfg.get(message.chat.id)
        if not cfg.auth:
            return await message.reply_text("📭 No authorised users. Admins can add some with /auth (reply to a user).")
        lines = []
        for uid in list(cfg.auth)[:40]:
            try:
                u = await client.get_users(uid)
                lines.append(f'• <a href="tg://user?id={uid}">{escape(u.first_name or str(uid))}</a> <code>{uid}</code>')
            except Exception:
                lines.append(f"• <code>{uid}</code>")
        await message.reply_text("🛡 <b>Authorised users</b>\n\n" + "\n".join(lines), parse_mode=HTML)

    # ---------------- song cache (owner) ----------------
    @app.on_message(filters.command("cache"))
    async def cache_cmd(client, message: Message):
        if not (message.from_user and is_owner(message.from_user.id)):
            return await message.reply_text("❌ Only the bot owner can use this.")
        if not cache.enabled:
            return await message.reply_text(
                "💾 Song cache is OFF. Set FIREBASE_URL (and MUSIC_CACHE=1) to turn it on.")
        if len(message.command) > 1 and message.command[1].lower() == "clear":
            n = await cache.clear()
            return await message.reply_text(f"🧹 Cleared {n} cached songs.")
        songs, mb = await cache.stats()
        from .settings import MUSIC_CACHE_MAX_MB
        await message.reply_text(
            f"💾 <b>Song cache</b>\n\n🎵 Songs: <b>{songs}</b>\n📦 Size: <b>{mb:.0f} / {MUSIC_CACHE_MAX_MB} MB</b>\n\n"
            "/cache clear - delete everything", parse_mode=HTML)

    # ---------------- live radio ----------------
    _radios = {}   # (chat_id, message_id) -> {"list": [...], "page": 0}

    async def _radio_start(chat_id: int, station, user, user_id: int):
        """Play a station right now. Returns None on success or an error text."""
        err = await music_player.ensure_assistant(chat_id)
        if err:
            return err
        track = Track(title=f"📻 {station.name}", url="", duration=0, thumb=station.logo, video=False,
                      requested_by=user, vid="", channel=station.genre or "Live radio",
                      requested_by_id=user_id, stream_url=station.url, live=True)
        track.thumb_task = asyncio.create_task(make_thumb(track))
        try:
            await music_player.play_or_queue(chat_id, track, now=True)
        except Exception as e:
            music_player.state.pop(chat_id, None)
            music_player._unbind(chat_id)
            await _drop_thumb(track)
            return f"Couldn't start the station: {escape(str(e)[:150])}"
        await music_player.announce(chat_id, track)
        return None

    async def _open_radio_picker(chat_id: int, stations, header: str):
        markup = radio_markup(stations, 0)
        text = (f"📻 <b>{header}</b>\n{len(stations)} live stations - tap one to tune in.\n"
                "<i>Or type /radio &lt;name or genre&gt; (e.g. /radio bollywood).</i>")
        sent = await app.send_message(chat_id, text, reply_markup=markup, parse_mode=HTML)
        _radios[(chat_id, sent.id)] = {"list": stations, "page": 0}
        while len(_radios) > 40:
            _radios.pop(next(iter(_radios)))
        await colorize(sent, markup, radio_styles(stations, 0))

    @app.on_message(filters.group & filters.command(["radio", "fm"]))
    async def radio_cmd(client, message: Message):
        if not music_player.enabled:
            return await message.reply_text("🎵 The music system isn't enabled on this bot.")
        if not await _can_play(client, message):
            return await message.reply_text("❌ Only admins can start music in this group right now.")
        arg = message.text.split(None, 1)[1].strip() if len(message.command) > 1 else ""
        if not arg:
            return await _open_radio_picker(message.chat.id, list(radio.stations()), "Live radio")
        status = await message.reply_text("📻 Tuning in...")
        try:
            station = await radio.find(arg)
        except Exception:
            station = None
        if not station:
            return await status.edit_text("❌ No station found. Try /radio to browse the list.")
        user = message.from_user.first_name if message.from_user else "Anonymous"
        err = await _radio_start(message.chat.id, station, user,
                                 message.from_user.id if message.from_user else 0)
        if err:
            return await status.edit_text(f"❌ {err}", parse_mode=HTML)
        try:
            await status.delete()
        except Exception:
            pass

    async def _radio_action(client, cq, action: str):
        chat_id, mid = cq.message.chat.id, cq.message.id
        rp = _radios.get((chat_id, mid))
        if action == "rdx":
            _radios.pop((chat_id, mid), None)
            try:
                await cq.message.delete()
            except Exception:
                pass
            return await cq.answer()
        if not rp:
            return await cq.answer("This list expired - send /radio again.", show_alert=True)
        if action.startswith("rdp:"):
            rp["page"] = int(action.split(":")[1])
            await cq.answer()
            return await colorize(cq.message, radio_markup(rp["list"], rp["page"]),
                                  radio_styles(rp["list"], rp["page"]))
        try:
            station = rp["list"][int(action.split(":")[1])]
        except (IndexError, ValueError):
            return await cq.answer("That station isn't available.", show_alert=True)
        if not music_player.enabled:
            return await cq.answer("Music is off.", show_alert=True)
        if not await _can_play_id(client, chat_id, cq.from_user.id):
            return await cq.answer("Only admins can start music in this group.", show_alert=True)
        await cq.answer(f"📻 Tuning in to {station.name[:40]}...")
        err = await _radio_start(chat_id, station, cq.from_user.first_name, cq.from_user.id)
        if err:
            return await app.send_message(chat_id, f"❌ {err}", parse_mode=HTML)
        _radios.pop((chat_id, mid), None)
        try:
            await cq.message.delete()
        except Exception:
            pass

    @app.on_message(filters.group & filters.command(["np", "nowplaying"]))
    async def np_cmd(client, message: Message):
        if not music_player.enabled:
            return
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("⚠️ Nothing is playing.")
        header = "⏸ <b>Paused</b>" if st.paused else "🎧 <b>Now playing</b>"
        await message.reply_text(music_player.now_text(st.current, header), parse_mode=HTML)

    # ---------------- autoplay / favourites commands ----------------
    @app.on_message(filters.group & filters.command(["autoplay", "autoqueue", "aq"]))
    async def autoplay_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text(NO_ADMIN)
        arg = message.command[1].lower() if len(message.command) > 1 else ""
        cid = message.chat.id
        if arg in ("on", "off"):
            if music_player.is_auto(cid) != (arg == "on"):
                music_player.toggle_auto(cid)
        else:
            music_player.toggle_auto(cid)
        on = music_player.is_auto(cid)
        await message.reply_text(
            "♾ Auto queue is <b>ON</b> - similar songs are added automatically, so the music never stops." if on
            else "♾ Auto queue is <b>OFF</b>.", parse_mode=HTML)

    @app.on_message(filters.command("favs"))
    async def favs_cmd(client, message: Message):
        if not message.from_user:
            return
        favs = await get_favs(message.from_user.id)
        if not favs:
            return await message.reply_text(
                "💔 You have no favourites yet. Tap ❤️ ꜰᴀᴠ under a playing song.")
        lines = [f"{i}. {escape(t[:60])} [{fmt_time(d)}]" for i, (_, t, d) in enumerate(favs[:30], 1)]
        await message.reply_text(
            "❤️ <b>Your favourites</b>\n\n" + "\n".join(lines) +
            "\n\nPlay one in a group with /playfav <number>", parse_mode=HTML)

    @app.on_message(filters.group & filters.command("playfav"))
    async def playfav_cmd(client, message: Message):
        if not message.from_user:
            return
        favs = await get_favs(message.from_user.id)
        if not favs:
            return await message.reply_text("💔 You have no favourites yet.")
        try:
            idx = int(message.command[1]) - 1
            vid = favs[idx][0]
        except (IndexError, ValueError):
            return await message.reply_text("⚠️ Usage: /playfav <number>  (see /favs)")
        await _play(client, message, False, query_override=f"https://www.youtube.com/watch?v={vid}")

    # ---------------- similar-songs picker (anyone can pick) ----------------
    _pickers = {}   # (chat_id, message_id) -> {"tracks": [...], "page": 0}

    async def _open_picker(chat_id, tracks, header, base_title):
        markup = picker_markup(tracks, 0)
        text = (f"🎵 <b>{header}</b>\n{escape(base_title)}\n\n"
                "Choose a song to add it to the queue or start playback.")
        sent = await app.send_message(chat_id, text, reply_markup=markup, parse_mode=HTML)
        _pickers[(chat_id, sent.id)] = {"tracks": tracks, "page": 0}
        while len(_pickers) > 60:
            _pickers.pop(next(iter(_pickers)))
        await colorize(sent, markup, picker_styles(tracks, 0))

    async def _suggest_after_end(chat_id, base):
        if not MUSIC_SUGGEST_AFTER_END:
            return
        tracks = await music_player.similar_tracks(chat_id, base=base)
        if tracks:
            await _open_picker(chat_id, tracks, "Songs similar to the track that just ended:", base.title)

    music_player.on_queue_end = _suggest_after_end

    async def _picker_action(client, cq, action):
        chat_id, mid = cq.message.chat.id, cq.message.id
        pk = _pickers.get((chat_id, mid))
        if action == "pkx":
            _pickers.pop((chat_id, mid), None)
            try:
                await cq.message.delete()
            except Exception:
                pass
            return await cq.answer()
        if not pk:
            return await cq.answer("This list expired - tap 🎵 Rec again.", show_alert=True)
        tracks = pk["tracks"]
        if action == "pkn":
            pk["page"] = (pk["page"] + 1) % picker_pages(len(tracks))
            await cq.answer()
            return await colorize(cq.message, picker_markup(tracks, pk["page"]),
                                  picker_styles(tracks, pk["page"]))
        try:
            track = copy.copy(tracks[int(action.split(":")[1])])
        except (IndexError, ValueError):
            return await cq.answer("That song isn't available.", show_alert=True)
        if not music_player.enabled:
            return await cq.answer("Music is off.", show_alert=True)
        st = music_player.state.get(chat_id)
        if st and len(st.queue) >= MUSIC_QUEUE_LIMIT:
            return await cq.answer("The queue is full.", show_alert=True)
        track.requested_by, track.file_path = cq.from_user.first_name, ""
        track.requested_by_id = cq.from_user.id
        err = await music_player.ensure_assistant(chat_id)
        if err:
            return await cq.answer(err[:190], show_alert=True)
        await cq.answer("⏳ Loading...")
        try:
            result, pos = await music_player.play_or_queue(chat_id, track)
        except Exception as e:
            music_player.state.pop(chat_id, None)
            return await app.send_message(
                chat_id, f"❌ Couldn't start playback: {escape(str(e))}", parse_mode=HTML)
        _pickers.pop((chat_id, mid), None)
        try:
            await cq.message.delete()
        except Exception:
            pass
        if result == "playing":
            await music_player.announce(chat_id, track)
        elif result == "duplicate":
            await app.send_message(chat_id, "♻️ That song is already " + (
                "playing." if pos == 0 else f"in the queue (position {pos})."))
        else:
            await _show_queued(track, pos, chat_id=chat_id)

    # ---------------- inline buttons under the now-playing card ----------------
    @app.on_callback_query(filters.regex(r"^mus:"))
    async def music_buttons(client, cq):
        action = cq.data.split(":", 1)[1]
        chat_id = cq.message.chat.id
        user = cq.from_user
        if action == "noop":            # the progress bar button does nothing
            return await cq.answer()
        if action == "del":             # DELETE under the 'added to queue' card
            try:
                await cq.message.delete()
            except Exception:
                pass
            return await cq.answer()
        if action.startswith("pk"):     # similar-songs picker (works even when nothing plays)
            return await _picker_action(client, cq, action)
        if action.startswith("rd"):     # live radio picker
            return await _radio_action(client, cq, action)
        if action == "qx":              # paged /queue
            try:
                await cq.message.delete()
            except Exception:
                pass
            return await cq.answer()
        if action.startswith("qp:"):
            st0 = music_player.state.get(chat_id)
            if not st0 or not st0.current:
                return await cq.answer("The queue is empty.", show_alert=True)
            pages = max(1, -(-len(st0.queue) // QUEUE_PAGE))
            page = max(0, min(int(action.split(":")[1]), pages - 1))
            await cq.answer()
            markup = queue_markup(len(st0.queue), page)
            try:
                await cq.message.edit_text(_queue_text(chat_id, st0, page), parse_mode=HTML,
                                           reply_markup=markup, **NO_PREVIEW)
            except Exception:
                pass
            return await colorize(cq.message, markup, queue_styles(len(st0.queue), page))
        if not music_player.enabled:
            return await cq.answer("Music is off.", show_alert=True)
        st = music_player.state.get(chat_id)
        if not st or not st.current:
            return await cq.answer("Nothing is playing right now.", show_alert=True)

        cfg = await chatcfg.get(chat_id)
        free = ("fav", "rec") + (("skip",) if cfg.skipmode == "all" else ())
        if action not in free:                 # fav + rec (+ skip by default) are open to everyone
            if not await _may_control(client, chat_id, user.id):
                return await cq.answer("Only admins and authorised users can use this button.", show_alert=True)

        try:
            if action == "pause":
                ok = await music_player.pause(chat_id)
                await cq.answer("⏸ Paused" if ok else "Already paused")
            elif action == "resume":
                ok = await music_player.resume(chat_id)
                await cq.answer("▶️ Resumed" if ok else "Not paused")
            elif action == "replay":
                await music_player.seek(chat_id, to=0)
                await cq.answer("🔁 Replaying from the start")
                await music_player.refresh_card(chat_id)
            elif action == "skip":
                await cq.answer("⏭ Skipped")
                await music_player.advance(chat_id, announce=True, skip=True)
            elif action == "stop":
                await cq.answer("⏹ Stopped")
                await music_player.end(chat_id)
            elif action in ("back", "fwd"):
                pos = await music_player.seek(chat_id, delta=-20 if action == "back" else 20)
                if pos == -1:
                    await cq.answer("Can't seek a live stream", show_alert=True)
                else:
                    await cq.answer(("⏪ " if action == "back" else "⏩ ") + fmt_time(pos))
                    await music_player.refresh_card(chat_id)
            elif action == "rec":
                await cq.answer("🔎 Finding similar songs...")
                tracks = await music_player.similar_tracks(chat_id)
                if tracks:
                    await _open_picker(chat_id, tracks, "Songs similar to the current track:", st.current.title)
                else:
                    await app.send_message(chat_id, "⚠️ Couldn't find similar songs.")
            elif action == "fav":
                ok = await add_fav(user.id, st.current)
                await cq.answer("❤️ Saved to your favourites (/favs)" if ok
                                else "Already in your favourites")
            elif action == "auto":
                on = music_player.toggle_auto(chat_id)
                markup = music_player.markup(chat_id)
                await cq.answer("♾ Auto queue ON" if on else "♾ Auto queue OFF")
                try:
                    await colorize(cq.message, markup, STYLES)   # one call - no plain flash
                except Exception:
                    pass
        except Exception as e:
            try:
                await cq.answer(f"Error: {str(e)[:150]}", show_alert=True)
            except Exception:
                pass
