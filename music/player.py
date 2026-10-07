# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: voice-chat player
# ============================================================
# One assistant (user) account joins group voice chats through
# py-tgcalls and streams audio/video. The bot itself handles commands.

import os
import time
import asyncio
import logging
from dataclasses import dataclass, field
from html import escape
from typing import Optional

from pyrogram import Client, enums, errors
from pytgcalls import PyTgCalls, types

from config import API_ID, API_HASH
from .settings import STRING_SESSION
from .youtube import Track, prepare, release, fmt_time, related_track, related_tracks, API_ENABLED
from .ui import controls, card_text, STYLES
from .thumbnail import make_thumb

log = logging.getLogger("music")

TICK_SECONDS = 10   # how often the progress button is refreshed


@dataclass
class ChatState:
    current: Optional[Track] = None
    queue: list = field(default_factory=list)
    loop: bool = False
    paused: bool = False
    last: Optional[Track] = None                   # last track that played (for autoplay)
    history: list = field(default_factory=list)    # recent video ids (autoplay/rec skip repeats)
    offset: float = 0.0                            # seconds into the track when `started` was set
    started: float = 0.0                           # monotonic time playback (re)started
    card: Optional[tuple] = None                   # (chat_id, message_id) of the now-playing card

    def position(self) -> int:
        if not self.current:
            return 0
        if self.paused:
            return int(self.offset)
        return int(self.offset + (time.monotonic() - self.started))


class MusicPlayer:
    def __init__(self):
        self.bot: Optional[Client] = None
        self.assistant: Optional[Client] = None
        self.calls: Optional[PyTgCalls] = None
        self.enabled = False
        self.state: dict[int, ChatState] = {}
        self._locks: dict[int, asyncio.Lock] = {}
        self._joined: set[int] = set()
        self._last_end: dict[int, float] = {}
        self.auto_chats: set[int] = set()          # chats with autoplay switched on
        self._tickers: dict[int, asyncio.Task] = {}   # live progress-bar updaters
        self.on_queue_end = None                      # async hook(chat_id, last_track) set by handlers

    # ---------------- lifecycle ----------------
    async def start(self, bot: Client):
        self.bot = bot
        from .ffmpeg_setup import ensure_ffmpeg
        ensure_ffmpeg()
        if not STRING_SESSION:
            log.warning("🎵 STRING_SESSION not set - music system disabled")
            return
        if not API_ENABLED:
            log.warning("🎵 MUSIC_API_KEY not set - music system disabled (the third-party API is the only audio source)")
            return
        self.assistant = Client(
            "elina_assistant",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=STRING_SESSION,
            in_memory=True,
        )
        await self.assistant.start()
        self.calls = PyTgCalls(self.assistant)

        @self.calls.on_update()
        async def _on_update(_, update: types.Update):
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    await self._on_stream_end(update.chat_id)
            elif isinstance(update, types.ChatUpdate):
                if update.status in (
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ):
                    self.state.pop(update.chat_id, None)
                    self._joined.discard(update.chat_id)

        await self.calls.start()
        self.enabled = True
        me = self.assistant.me
        log.info(f"🎵 Music ready - assistant @{me.username or me.first_name}")

    async def stop(self):
        try:
            if self.assistant and self.assistant.is_connected:
                await self.assistant.stop()
        except Exception:
            pass

    def _lock(self, chat_id: int) -> asyncio.Lock:
        return self._locks.setdefault(chat_id, asyncio.Lock())

    # ---------------- assistant membership ----------------
    async def ensure_assistant(self, chat_id: int) -> Optional[str]:
        """Make sure the assistant account is in the group.
        Returns None on success, or a user-facing error string."""
        if chat_id in self._joined:
            return None
        me = self.assistant.me
        try:
            member = await self.bot.get_chat_member(chat_id, me.id)
            if member.status == enums.ChatMemberStatus.BANNED:
                return "The assistant account is banned in this group. Unban it first."
            if member.status not in (
                enums.ChatMemberStatus.LEFT,
                enums.ChatMemberStatus.RESTRICTED,
            ):
                self._joined.add(chat_id)
                return None
        except errors.UserNotParticipant:
            pass
        except Exception:
            pass  # bot may lack rights to look - just try joining

        try:
            chat = await self.bot.get_chat(chat_id)
            link = chat.username or chat.invite_link
            if not link:
                link = await self.bot.export_chat_invite_link(chat_id)
        except Exception:
            return ("I couldn't create an invite for the assistant. Make me an admin "
                    "with 'Invite users', or add the assistant account manually.")
        try:
            await self.assistant.join_chat(link)
        except errors.UserAlreadyParticipant:
            pass
        except errors.InviteRequestSent:
            try:
                await self.bot.approve_chat_join_request(chat_id, me.id)
            except Exception:
                return "Join request sent - please approve the assistant account."
        except Exception as e:
            return f"The assistant couldn't join this group: {e}"
        self._joined.add(chat_id)
        return None

    # ---------------- playback ----------------
    async def _start_stream(self, chat_id: int, track: Track, seek: int = 0):
        url = await prepare(track)
        stream = types.MediaStream(
            media_path=url,
            audio_parameters=getattr(types.AudioQuality, "STUDIO", types.AudioQuality.HIGH),   # 48 kHz stereo
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(types.MediaStream.Flags.AUTO_DETECT if track.video
                         else types.MediaStream.Flags.IGNORE),
            ffmpeg_parameters=(f"-ss {seek} " if seek > 1 else "")
            + "-probesize 10M -analyzeduration 5M -fflags +genpts",
        )
        last_exc = None
        for attempt in range(3):
            try:
                await self.calls.play(
                    chat_id, stream, config=types.GroupCallConfig(auto_start=True)
                )
                return
            except Exception as e:  # voice chat may still be starting
                last_exc = e
                await asyncio.sleep(1.5)
        raise last_exc

    def now_text(self, track: Track, header: str) -> str:
        link = f'<a href="{escape(track.url)}">{escape(track.title)}</a>' if track.url else escape(track.title)
        return (
            f"{header}\n\n🎵 <b>{link}</b>\n"
            f"⏱ {fmt_time(track.duration)}  •  👤 {escape(track.requested_by)}"
        )

    async def play_or_queue(self, chat_id: int, track: Track) -> tuple[str, int]:
        """Returns ('playing', 0) or ('queued', position)."""
        async with self._lock(chat_id):
            st = self.state.setdefault(chat_id, ChatState())
            if st.current is None:
                await self._start_stream(chat_id, track)
                self._begin(st, track)
                return "playing", 0
            st.queue.append(track)
            return "queued", len(st.queue)

    async def _on_stream_end(self, chat_id: int):
        now = time.time()
        if now - self._last_end.get(chat_id, 0) < 2:   # dedupe duplicate events
            return
        self._last_end[chat_id] = now
        await self.advance(chat_id, announce=True)

    def _begin(self, st: ChatState, track: Track):
        st.current, st.last, st.paused = track, track, False
        st.offset, st.started = 0.0, time.monotonic()
        if track.vid:
            st.history = (st.history + [track.vid])[-50:]

    async def advance(self, chat_id: int, announce: bool = True, skip: bool = False) -> Optional[Track]:
        """Move to next track (or repeat if loop, or autoplay a similar one)."""
        async with self._lock(chat_id):
            st = self.state.get(chat_id)
            if not st:
                return None
            ended = st.current
            auto_tries = 0
            while True:
                if st.loop and not skip and ended and st.current is ended:
                    nxt = ended
                elif st.queue:
                    nxt = st.queue.pop(0)
                else:
                    base = ended or st.last
                    if self.is_auto(chat_id) and base and auto_tries < 3:
                        auto_tries += 1
                        rel = await related_track(base, set(st.history), "Autoplay")
                        if rel:
                            st.queue.append(rel)
                            continue
                    if ended is not None:
                        release(ended)
                    st.current = None
                    await self._drop_card(st)
                    try:
                        await self.calls.leave_call(chat_id)
                    except Exception:
                        pass
                    self.state.pop(chat_id, None)
                    if announce:
                        await self._say(chat_id, "✅ Queue finished - leaving the voice chat.")
                        if self.on_queue_end and base:
                            try:
                                await self.on_queue_end(chat_id, base)
                            except Exception:
                                log.warning("queue-end suggestions failed", exc_info=True)
                    return None
                try:
                    await self._start_stream(chat_id, nxt)
                    if ended is not None and ended is not nxt:
                        release(ended, st.queue + [nxt])
                    self._begin(st, nxt)
                    if announce:
                        await self.announce(chat_id, nxt)
                    return nxt
                except Exception as e:
                    log.warning(f"track failed in {chat_id}: {e}")
                    await self._say(chat_id, f"⚠️ Couldn't play <b>{escape(nxt.title)}</b>, skipping.")
                    ended = None
                    st.current = None

    # ---------------- now-playing card ----------------
    async def _drop_card(self, st: Optional[ChatState]):
        if st and st.card:
            self._stop_ticker(st.card[0])
            try:
                await self.bot.delete_messages(*st.card)
            except Exception:
                pass
            st.card = None

    async def announce(self, chat_id: int, track: Track):
        """Send the 'started streaming' card (thumbnail + caption + buttons)."""
        st = self.state.get(chat_id)
        await self._drop_card(st)
        markup = self.markup(chat_id)
        caption = card_text(track)
        path = await make_thumb(track)
        sent = None
        try:
            if path:
                sent = await self.bot.send_photo(
                    chat_id, path, caption=caption, reply_markup=markup,
                    parse_mode=enums.ParseMode.HTML)
            else:
                sent = await self.bot.send_message(
                    chat_id, caption, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
        except Exception as e:
            log.warning(f"announce failed in {chat_id}: {e}")
        finally:
            if path:
                try:
                    os.remove(path)
                except OSError:
                    pass
        if sent:
            if st:
                st.card = (chat_id, sent.id)
            try:
                from handlers.colorui import colorize
                await colorize(sent, markup, STYLES)
            except Exception:
                pass
            if st and track.duration:
                self._start_ticker(chat_id)

    def markup(self, chat_id: int):
        """Keyboard for the card, reflecting the current position + autoplay state."""
        st = self.state.get(chat_id)
        pos = st.position() if st else 0
        dur = st.current.duration if st and st.current else 0
        return controls(self.is_auto(chat_id), self.bot.me.username or "", pos, dur)

    async def refresh_card(self, chat_id: int):
        """Redraw the card's buttons (progress bar) right now."""
        st = self.state.get(chat_id)
        if not st or not st.card or not st.current:
            return
        try:
            from types import SimpleNamespace
            from handlers.colorui import colorize
            msg = SimpleNamespace(chat=SimpleNamespace(id=st.card[0]), id=st.card[1])
            await colorize(msg, self.markup(chat_id), STYLES)
        except Exception:
            pass

    def _start_ticker(self, chat_id: int):
        self._stop_ticker(chat_id)
        self._tickers[chat_id] = asyncio.create_task(self._tick(chat_id))

    def _stop_ticker(self, chat_id: int):
        t = self._tickers.pop(chat_id, None)
        if t and not t.done():
            t.cancel()

    async def _tick(self, chat_id: int):
        try:
            while True:
                await asyncio.sleep(TICK_SECONDS)
                st = self.state.get(chat_id)
                if not st or not st.current or not st.card:
                    return
                if st.paused or not st.current.duration:
                    continue
                await self.refresh_card(chat_id)
        except asyncio.CancelledError:
            pass

    # ---------------- autoplay / recommendations / seek ----------------
    def is_auto(self, chat_id: int) -> bool:
        return chat_id in self.auto_chats

    def toggle_auto(self, chat_id: int) -> bool:
        if chat_id in self.auto_chats:
            self.auto_chats.discard(chat_id)
            return False
        self.auto_chats.add(chat_id)
        return True

    async def similar_tracks(self, chat_id: int, base: Optional[Track] = None, limit: int = 16) -> list:
        """Songs similar to `base` (default: the current track) for the picker."""
        st = self.state.get(chat_id)
        base = base or (st.current if st else None)
        if not base:
            return []
        exclude = set(st.history[-10:]) if st else set()
        return await related_tracks(base, exclude, limit=limit, user="Rec")

    async def seek(self, chat_id: int, delta: int = 0, to: Optional[int] = None) -> Optional[int]:
        """Jump by `delta` seconds (or to `to`). Returns the new position,
        -1 for a live stream, None if nothing is playing."""
        async with self._lock(chat_id):
            st = self.state.get(chat_id)
            if not st or not st.current:
                return None
            tr = st.current
            if not tr.duration:
                return -1
            new = to if to is not None else st.position() + delta
            new = max(0, min(int(new), max(tr.duration - 3, 0)))
            await self._start_stream(chat_id, tr, seek=new)
            st.offset, st.started, st.paused = float(new), time.monotonic(), False
            return new

    async def pause(self, chat_id: int) -> bool:
        st = self.state.get(chat_id)
        if not st or not st.current or st.paused:
            return False
        pos = st.position()
        await self.calls.pause(chat_id)
        st.offset, st.paused = float(pos), True
        return True

    async def resume(self, chat_id: int) -> bool:
        st = self.state.get(chat_id)
        if not st or not st.current or not st.paused:
            return False
        await self.calls.resume(chat_id)
        st.started, st.paused = time.monotonic(), False
        return True

    async def end(self, chat_id: int) -> bool:
        async with self._lock(chat_id):
            st = self.state.pop(chat_id, None)
            had = st is not None
            if st:
                await self._drop_card(st)
                for t in ([st.current] if st.current else []) + st.queue:
                    release(t)
            try:
                await self.calls.leave_call(chat_id)
            except Exception:
                pass
            return had

    async def _say(self, chat_id: int, text: str):
        try:
            await self.bot.send_message(
                chat_id, text, parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass


music_player = MusicPlayer()
