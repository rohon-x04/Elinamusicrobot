# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: commands
# ============================================================
# /play /vplay /pause /resume /skip /end /queue /loop /np /autoplay /favs /playfav
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
from .settings import (MUSIC_DURATION_LIMIT, MUSIC_QUEUE_LIMIT, MUSIC_FREE_SKIP,
                       MUSIC_SUGGEST_AFTER_END)
from handlers.common import is_admin, is_anonymous_admin
from .player import music_player
from .youtube import search_track, prefetch, fmt_time, StreamError
from .thumbnail import make_thumb
from .ui import (controls, STYLES, picker_markup, picker_styles, picker_pages,
                 queued_text, queued_markup, QUEUED_STYLES)
from .favs import get_favs, add_fav

HTML = enums.ParseMode.HTML


async def _can_control(client, message: Message) -> bool:
    if is_anonymous_admin(message):
        return True
    user = message.from_user
    if not user:
        return False
    if is_owner(user.id):
        return True
    return await is_admin(client, message.chat.id, user.id)



def register_music_handlers(app: Client):

    async def _show_queued(track, pos, status=None, chat_id=None):
        """'Added to queue' card with ▷ ⏸ >> ▢ and DELETE buttons."""
        text, markup = queued_text(track, pos), queued_markup()
        if status is not None:
            if await edit_styled(status, text, markup, QUEUED_STYLES, parse_mode="HTML"):
                return                      # edited + coloured in one call
            sent = await status.edit_text(text, reply_markup=markup, parse_mode=HTML,
                                          disable_web_page_preview=True)
        else:
            sent = await app.send_message(chat_id, text, reply_markup=markup, parse_mode=HTML,
                                          disable_web_page_preview=True)
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

    async def _play(client: Client, message: Message, video: bool, query_override: str = ""):
        if not music_player.enabled:
            return await message.reply_text("🎵 The music system isn't enabled on this bot.")

        query = query_override or (
            message.text.split(None, 1)[1].strip() if len(message.command) > 1 else "")
        if not query and message.reply_to_message:
            r = message.reply_to_message
            query = (r.text or r.caption or "").strip()
        if not query:
            return await message.reply_text(
                "⚠️ Usage: /play <song name or YouTube link>\n/vplay for video.")

        user = message.from_user.first_name if message.from_user else "Anonymous"
        status = await message.reply_text("🔎 Searching...")

        try:
            track = await search_track(query, video, user)
            track.requested_by_id = message.from_user.id if message.from_user else 0
        except Exception:
            return await status.edit_text("❌ Couldn't find or load that. Try another name or link.")

        if not track.duration:
            return await status.edit_text("❌ Live streams aren't supported - send a normal song or video.")

        if MUSIC_DURATION_LIMIT and track.duration and track.duration > MUSIC_DURATION_LIMIT * 60:
            return await status.edit_text(
                f"❌ Too long. The limit is {MUSIC_DURATION_LIMIT} minutes.")

        st = music_player.state.get(message.chat.id)
        if st and len(st.queue) >= MUSIC_QUEUE_LIMIT:
            return await status.edit_text(f"❌ The queue is full ({MUSIC_QUEUE_LIMIT} tracks).")

        # Start the download and draw the thumbnail NOW, while the assistant joins the group.
        if not (st and st.current):
            prefetch(track)
            track.thumb_task = asyncio.create_task(make_thumb(track))

        err = await music_player.ensure_assistant(message.chat.id)
        if err:
            await _drop_thumb(track)
            return await status.edit_text(f"❌ {err}")

        try:
            result, pos = await music_player.play_or_queue(message.chat.id, track)
        except Exception as e:
            music_player.state.pop(message.chat.id, None)
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
            await music_player.announce(message.chat.id, track)   # thumbnail card + buttons
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
            return await message.reply_text("❌ Only admins can use this.")
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
            return await message.reply_text("❌ Only admins can use this.")
        try:
            ok = await music_player.resume(message.chat.id)
        except Exception:
            ok = False
        await message.reply_text("▶️ Resumed." if ok else "⚠️ Nothing is paused.")

    @app.on_message(filters.group & filters.command(["skip", "next"]))
    async def skip_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not MUSIC_FREE_SKIP and not await _can_control(client, message):
            return await message.reply_text("❌ Only admins can use this.")
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("⚠️ Nothing is playing.")
        await music_player.advance(message.chat.id, announce=True, skip=True)

    @app.on_message(filters.group & filters.command(["end", "stopmusic"]))
    async def end_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text("❌ Only admins can use this.")
        ok = await music_player.end(message.chat.id)
        await message.reply_text("⏹ Stopped and cleared the queue." if ok else "⚠️ Nothing is playing.")

    @app.on_message(filters.group & filters.command("loop"))
    async def loop_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text("❌ Only admins can use this.")
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("⚠️ Nothing is playing.")
        st.loop = not st.loop
        await message.reply_text("🔁 Loop on - current track repeats." if st.loop else "➡️ Loop off.")

    @app.on_message(filters.group & filters.command(["queue", "q"]))
    async def queue_cmd(client, message: Message):
        if not music_player.enabled:
            return
        st = music_player.state.get(message.chat.id)
        if not st or not st.current:
            return await message.reply_text("📭 The queue is empty.")
        lines = [f"▶️ <b>{escape(st.current.title)}</b> [{fmt_time(st.current.duration)}]"]
        for i, t in enumerate(st.queue[:15], 1):
            lines.append(f"{i}. {escape(t.title)} [{fmt_time(t.duration)}]")
        if len(st.queue) > 15:
            lines.append(f"…and {len(st.queue) - 15} more")
        await message.reply_text("🎶 <b>Queue</b>\n\n" + "\n".join(lines), parse_mode=HTML)

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
    @app.on_message(filters.group & filters.command("autoplay"))
    async def autoplay_cmd(client, message: Message):
        if not music_player.enabled:
            return
        if not await _can_control(client, message):
            return await message.reply_text("❌ Only admins can use this.")
        arg = message.command[1].lower() if len(message.command) > 1 else ""
        cid = message.chat.id
        if arg in ("on", "off"):
            if music_player.is_auto(cid) != (arg == "on"):
                music_player.toggle_auto(cid)
        else:
            music_player.toggle_auto(cid)
        on = music_player.is_auto(cid)
        await message.reply_text(
            "♾ Autoplay is <b>ON</b> - similar songs keep playing when the queue ends." if on
            else "♾ Autoplay is <b>OFF</b>.", parse_mode=HTML)

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
        if not music_player.enabled:
            return await cq.answer("Music is off.", show_alert=True)
        st = music_player.state.get(chat_id)
        if not st or not st.current:
            return await cq.answer("Nothing is playing right now.", show_alert=True)

        free = ("fav", "rec") + (("skip",) if MUSIC_FREE_SKIP else ())
        if action not in free:                 # fav + rec (+ skip by default) are open to everyone
            if not (is_owner(user.id) or await is_admin(client, chat_id, user.id)):
                return await cq.answer("Only admins can use this button.", show_alert=True)

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
                await cq.answer("♾ Autoplay ON" if on else "♾ Autoplay OFF")
                try:
                    await colorize(cq.message, markup, STYLES)   # one call - no plain flash
                except Exception:
                    pass
        except Exception as e:
            try:
                await cq.answer(f"Error: {str(e)[:150]}", show_alert=True)
            except Exception:
                pass
