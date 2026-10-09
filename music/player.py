# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: voice-chat player
# ============================================================
# One assistant (user) account joins group voice chats through
# py-tgcalls and streams audio/video. The bot itself handles commands.

import os
import random
import time
import asyncio
import logging
from dataclasses import dataclass, field
from html import escape
from typing import Optional

from pyrogram import Client, enums, errors
from pytgcalls import PyTgCalls, types

from config import API_ID, API_HASH
from .settings import (STRING_SESSIONS, MUSIC_AUDIO_QUALITY, MUSIC_PREFETCH,
                       MUSIC_AUTO_MIN, MUSIC_AUTO_BATCH)
from .youtube import (Track, source, prefetch, release, fmt_time, related_track, related_tracks,
                      API_ENABLED)
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
    direct: bool = False                           # current stream is read live from a URL
    volume: int = 100                              # 1-200 (%)
    muted: bool = False
    retries: int = 0                               # restart attempts for the current stream

    def position(self) -> int:
        if not self.current:
            return 0
        if self.paused:
            return int(self.offset)
        return int(self.offset + (time.monotonic() - self.started))


@dataclass(eq=False)
class Assistant:
    """One assistant (user) account + its own voice-call engine."""
    session: str
    client: Client
    calls: PyTgCalls
    chats: set = field(default_factory=set)      # chats it is streaming in right now
    joined: set = field(default_factory=set)     # chats it is known to be a member of

    @property
    def me(self):
        return self.client.me

    @property
    def tag(self) -> str:
        me = self.client.me
        return f"@{me.username}" if me and me.username else (me.first_name if me else "?")


class MusicPlayer:
    def __init__(self):
        self.bot: Optional[Client] = None
        self.assistants: list = []                    # every running Assistant (multi-assistants)
        self.state: dict[int, ChatState] = {}
        self._bind: dict[int, Assistant] = {}         # chat -> the assistant serving it
        self._locks: dict[int, asyncio.Lock] = {}
        self._last_end: dict[int, float] = {}
        self._filling: set[int] = set()               # chats with an auto-queue refill running
        self.auto_chats: set[int] = set()             # chats with autoplay / auto queue switched on
        self._tickers: dict[int, asyncio.Task] = {}   # live progress-bar updaters
        self.on_queue_end = None                      # async hook(chat_id, last_track) set by handlers

    # ---- compatibility: the "main" assistant (ping card, /setstring result ...) ----
    @property
    def enabled(self) -> bool:
        return bool(self.assistants)

    @property
    def assistant(self) -> Optional[Client]:
        return self.assistants[0].client if self.assistants else None

    @property
    def calls(self) -> Optional[PyTgCalls]:
        return self.assistants[0].calls if self.assistants else None

    def _a(self, chat_id: int) -> Assistant:
        a = self._bind.get(chat_id)
        if a is None or a not in self.assistants:
            raise RuntimeError("no assistant is attached to this chat yet")
        return a

    # ---------------- lifecycle ----------------
    async def start(self, bot: Client):
        self.bot = bot
        from .ffmpeg_setup import ensure_ffmpeg
        ensure_ffmpeg()
        sessions = []
        try:
            import db
            sessions += await db.get_string_sessions()   # saved with /setstring
        except Exception as e:
            log.warning(f"🎵 could not read saved sessions: {e}")
        for s_ in STRING_SESSIONS:                        # env vars are added too
            if s_ not in sessions:
                sessions.append(s_)
        if not sessions:
            log.warning("🎵 No assistant session yet - send /setstring <session> to the bot in DM. Music disabled")
            return
        if not API_ENABLED:
            log.warning("🎵 MUSIC_API_KEY not set - music system disabled (the third-party API is the only audio source)")
            return
        results = await asyncio.gather(*[self._attach(x) for x in sessions])
        for x, (a, err) in zip(sessions, results):
            if err:
                log.warning(f"🎵 an assistant failed to start: {err}")
        log.info(f"🎵 {len(self.assistants)} assistant(s) ready")
        try:
            from . import radio
            radio.start_background_refresh()
        except Exception as e:
            log.warning(f"📻 radio refresh not started: {e}")

    async def _attach(self, session: str) -> tuple:
        """Start an assistant with this session string and add it to the pool.
        Returns (Assistant | None, error text | None)."""
        if any(a.session == session for a in self.assistants):
            return None, "This session is already active."
        client = Client(
            f"elina_assistant_{len(self.assistants)}_{abs(hash(session)) % 10**6}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=session,
            in_memory=True,
        )
        try:
            await client.start()
        except Exception as e:
            try:
                await client.stop()
            except Exception:
                pass
            return None, f"{type(e).__name__}: {e}"

        calls = PyTgCalls(client)
        asst = Assistant(session=session, client=client, calls=calls)

        @calls.on_update()
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
                    self._forget_chat(update.chat_id, asst)

        try:
            await calls.start()
        except Exception as e:
            try:
                await client.stop()
            except Exception:
                pass
            return None, f"{type(e).__name__}: {e}"

        self.assistants.append(asst)
        log.info(f"🎵 Assistant ready - {asst.tag}")
        return asst, None

    def _forget_chat(self, chat_id: int, asst: Assistant):
        """The call is over for this chat (kicked / voice chat closed): drop its state."""
        st = self.state.pop(chat_id, None)
        self._stop_ticker(chat_id)
        if self._bind.get(chat_id) is asst:
            self._bind.pop(chat_id, None)
        asst.chats.discard(chat_id)
        asst.joined.discard(chat_id)
        if st:
            for t in ([st.current] if st.current else []) + st.queue:
                release(t)

    async def _detach(self, asst: Assistant):
        """Stop one assistant and forget every chat it was serving."""
        if asst in self.assistants:
            self.assistants.remove(asst)
        for cid in list(asst.chats | {c for c, a in self._bind.items() if a is asst}):
            self._forget_chat(cid, asst)
        try:
            if asst.client.is_connected:
                await asst.client.stop()
        except Exception:
            pass

    # ---- used by /setstring, /delstring, /assistants ----
    async def set_session(self, session: str) -> Optional[str]:
        """Add another assistant account live (no restart). None = ok, else error text."""
        if not API_ENABLED:
            return "MUSIC_API_KEY is not set, so music can't run yet."
        asst, err = await self._attach(session)
        if err:
            return err
        try:
            import db
            await db.add_string_session(session)
        except Exception as e:
            log.warning(f"could not save the session: {e}")
        return None

    @property
    def last_added(self) -> Optional[Assistant]:
        return self.assistants[-1] if self.assistants else None

    async def remove_session(self, number: Optional[int] = None) -> Optional[str]:
        """Remove assistant #number (1-based) or all of them. Returns an error text or None."""
        import db
        if number is None:
            for a in list(self.assistants):
                await self._detach(a)
            await db.clear_string_sessions()
            return None
        if not 1 <= number <= len(self.assistants):
            return f"There is no assistant #{number}."
        a = self.assistants[number - 1]
        await self._detach(a)
        await db.remove_string_session(a.session)
        return None

    async def stop(self):
        for a in list(self.assistants):
            try:
                if a.client.is_connected:
                    await a.client.stop()
            except Exception:
                pass

    def _lock(self, chat_id: int) -> asyncio.Lock:
        return self._locks.setdefault(chat_id, asyncio.Lock())

    # ---------------- assistant membership ----------------
    async def _try_join(self, a: Assistant, chat_id: int) -> Optional[str]:
        """Make sure assistant `a` is in the group. None on success, else a user-facing error."""
        if chat_id in a.joined:
            return None
        me = a.me
        try:
            member = await self.bot.get_chat_member(chat_id, me.id)
            if member.status == enums.ChatMemberStatus.BANNED:
                return f"The assistant {a.tag} is banned in this group. Unban it first."
            if member.status not in (
                enums.ChatMemberStatus.LEFT,
                enums.ChatMemberStatus.RESTRICTED,
            ):
                a.joined.add(chat_id)
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
            await a.client.join_chat(link)
        except errors.UserAlreadyParticipant:
            pass
        except errors.InviteRequestSent:
            try:
                await self.bot.approve_chat_join_request(chat_id, me.id)
            except Exception:
                return "Join request sent - please approve the assistant account."
        except Exception as e:
            return f"The assistant {a.tag} couldn't join this group: {e}"
        a.joined.add(chat_id)
        return None

    async def _probe(self, a: Assistant, chat_id: int):
        """Quietly note whether assistant `a` is already a member of the group."""
        try:
            member = await self.bot.get_chat_member(chat_id, a.me.id)
            if member.status not in (enums.ChatMemberStatus.LEFT, enums.ChatMemberStatus.RESTRICTED,
                                     enums.ChatMemberStatus.BANNED):
                a.joined.add(chat_id)
        except Exception:
            pass

    async def ensure_assistant(self, chat_id: int) -> Optional[str]:
        """Pick the assistant for this group (multi-assistants) and make sure it is a member.
        A group keeps the same assistant while it is playing; a new group gets one that is
        already inside it, otherwise the least busy one. Returns None or an error string."""
        if not self.assistants:
            return "No assistant account is set up."
        cur = self._bind.get(chat_id)
        if cur in self.assistants and chat_id in cur.joined:
            return None
        # already-members first, then the least busy
        await asyncio.gather(*[self._probe(a, chat_id) for a in self.assistants
                               if chat_id not in a.joined])
        order = sorted(self.assistants, key=lambda a: (chat_id not in a.joined, len(a.chats)))
        last_err = None
        for a in order:
            err = await self._try_join(a, chat_id)
            if err is None:
                self._bind[chat_id] = a
                return None
            last_err = err
        return last_err

    # ---------------- playback ----------------
    def _audio_quality(self):
        """Audio profile for the voice chat. Automatic = best one that is 48 kHz stereo
        (works the same on py-tgcalls 2.x and 3.x)."""
        aq = types.AudioQuality
        if MUSIC_AUDIO_QUALITY:
            chosen = getattr(aq, MUSIC_AUDIO_QUALITY, None)
            if chosen is not None:
                return chosen
        for name in ("STUDIO", "HIGH"):
            q = getattr(aq, name, None)
            if q is None:
                continue
            val = getattr(q, "value", q)
            try:
                rate, channels = val[0], val[1]
            except (TypeError, IndexError, KeyError):
                return q                      # unknown shape: trust the library's name
            if rate <= 48000 and channels >= 2:
                return q
        return aq.HIGH

    @staticmethod
    def _ffmpeg_args(track: Track, direct: bool, seek: int) -> str:
        """Input options for ffmpeg. Small probe sizes = the first sound comes out fast;
        reconnect flags keep a network stream alive through short drops."""
        args = []
        if seek > 1:
            args.append(f"-ss {seek}")
        if direct:
            args.append("-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -rw_timeout 15000000")
        if track.video:
            args.append("-probesize 10M -analyzeduration 5M")
        else:
            args.append("-probesize 128k -analyzeduration 500000")
        args.append("-fflags +genpts")
        return " ".join(args)

    async def _start_stream(self, chat_id: int, track: Track, seek: int = 0):
        a = self._a(chat_id)
        src, direct = await source(track)
        stream = types.MediaStream(
            media_path=src,
            audio_parameters=self._audio_quality(),              # 48 kHz stereo -> Telegram Opus
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(types.MediaStream.Flags.AUTO_DETECT if track.video
                         else types.MediaStream.Flags.IGNORE),
            ffmpeg_parameters=self._ffmpeg_args(track, direct, seek),
        )
        last_exc = None
        for attempt in range(3):
            try:
                await a.calls.play(
                    chat_id, stream, config=types.GroupCallConfig(auto_start=True)
                )
                a.chats.add(chat_id)
                st = self.state.get(chat_id)
                if st:
                    st.direct = direct
                    await self._apply_volume(chat_id, st)
                return
            except Exception as e:  # voice chat may still be starting
                last_exc = e
                await asyncio.sleep(1.0 + attempt * 0.7)
        raise last_exc

    async def _apply_volume(self, chat_id: int, st: ChatState):
        """Re-apply volume / mute after a (re)started stream. Best effort."""
        try:
            a = self._a(chat_id)
            if st.volume != 100:
                await a.calls.change_volume_call(chat_id, st.volume)
            if st.muted:
                await a.calls.mute(chat_id)
        except Exception:
            pass

    def now_text(self, track: Track, header: str) -> str:
        link = f'<a href="{escape(track.url)}">{escape(track.title)}</a>' if track.url else escape(track.title)
        return (
            f"{header}\n\n🎵 <b>{link}</b>\n"
            f"⏱ {fmt_time(track.duration)}  •  👤 {escape(track.requested_by)}"
        )

    # ---- queue helpers ----
    @staticmethod
    def _same(a: Track, b: Track) -> bool:
        if a.stream_url or b.stream_url:
            return a.stream_url == b.stream_url
        return bool(a.vid) and a.vid == b.vid and a.video == b.video

    def _warm_queue(self, st: ChatState):
        """The first MUSIC_PREFETCH songs in line are downloaded before they're needed."""
        for t in st.queue[:MUSIC_PREFETCH]:
            prefetch(t)

    async def play_or_queue(self, chat_id: int, track: Track, front: bool = False,
                            now: bool = False) -> tuple[str, int]:
        """Returns ('playing', 0), ('queued', position) or ('duplicate', position).
        front=True puts the song first in line (/playnext); now=True plays it right away
        and leaves the queue untouched (used by live radio)."""
        async with self._lock(chat_id):
            st = self.state.setdefault(chat_id, ChatState())
            if now and st.current is not None:
                old = st.current
                await self._start_stream(chat_id, track)
                release(old, st.queue + [track])
                self._begin(chat_id, st, track)
                return "playing", 0
            if st.current is None:
                await self._start_stream(chat_id, track)
                self._begin(chat_id, st, track)
                return "playing", 0
            # smart queue: never add the same song twice
            if self._same(st.current, track):
                return "duplicate", 0
            for i, q in enumerate(st.queue, 1):
                if self._same(q, track):
                    return "duplicate", i
            if front:
                st.queue.insert(0, track)
            else:
                st.queue.append(track)
            self._warm_queue(st)
            return "queued", (1 if front else len(st.queue))

    async def _on_stream_end(self, chat_id: int):
        now = time.time()
        if now - self._last_end.get(chat_id, 0) < 2:   # dedupe duplicate events
            return
        self._last_end[chat_id] = now
        st = self.state.get(chat_id)
        if st and st.current and not st.paused:
            tr = st.current
            ran = time.monotonic() - st.started
            # a network stream that died right away -> try again (radio) / fall back to a download
            if tr.live and st.retries < 3:
                st.retries += 1
                async with self._lock(chat_id):
                    try:
                        await asyncio.sleep(1.5)
                        await self._start_stream(chat_id, tr)
                        st.started = time.monotonic()
                        return
                    except Exception as e:
                        log.warning(f"radio restart failed in {chat_id}: {e}")
            elif st.direct and ran < 6 and tr.duration > 15 and not tr.force_dl and st.offset == 0:
                tr.force_dl = True
                async with self._lock(chat_id):
                    try:
                        await self._start_stream(chat_id, tr)
                        st.started = time.monotonic()
                        log.info(f"direct stream failed in {chat_id}, playing the downloaded file")
                        return
                    except Exception as e:
                        log.warning(f"download fallback failed in {chat_id}: {e}")
        await self.advance(chat_id, announce=True)

    def _begin(self, chat_id: int, st: ChatState, track: Track):
        st.current, st.last, st.paused = track, track, False
        st.offset, st.started, st.retries = 0.0, time.monotonic(), 0
        if track.vid:
            st.history = (st.history + [track.vid])[-50:]
        self._warm_queue(st)               # the next songs download while this one plays
        self._autofill(chat_id)

    async def advance(self, chat_id: int, announce: bool = True, skip: bool = False) -> Optional[Track]:
        """Move to next track (or repeat if loop, or autoplay a similar one)."""
        async with self._lock(chat_id):
            st = self.state.get(chat_id)
            if not st:
                return None
            ended = st.current
            auto_tries = 0
            while True:
                if st.loop and not skip and ended and st.current is ended and not ended.live:
                    nxt = ended
                elif st.queue:
                    nxt = st.queue.pop(0)
                else:
                    base = ended or st.last
                    if self.is_auto(chat_id) and base and not base.live and auto_tries < 3:
                        auto_tries += 1
                        rel = await related_track(base, set(st.history), "Auto Queue")
                        if rel:
                            st.queue.append(rel)
                            continue
                    if ended is not None:
                        release(ended)
                    st.current = None
                    await self._drop_card(st)
                    try:
                        await self._a(chat_id).calls.leave_call(chat_id)
                    except Exception:
                        pass
                    self._unbind(chat_id)
                    self.state.pop(chat_id, None)
                    if announce:
                        await self._say(chat_id, "✅ Queue finished - leaving the voice chat.")
                        if self.on_queue_end and base and not base.live:
                            try:
                                await self.on_queue_end(chat_id, base)
                            except Exception:
                                log.warning("queue-end suggestions failed", exc_info=True)
                    return None
                try:
                    await self._start_stream(chat_id, nxt)
                    if ended is not None and ended is not nxt:
                        release(ended, st.queue + [nxt])
                    self._begin(chat_id, st, nxt)
                    if announce:
                        await self.announce(chat_id, nxt)
                    return nxt
                except Exception as e:
                    log.warning(f"track failed in {chat_id}: {e}")
                    await self._say(chat_id, f"⚠️ Couldn't play <b>{escape(nxt.title)}</b>, skipping.")
                    ended = None
                    st.current = None

    def _unbind(self, chat_id: int):
        a = self._bind.pop(chat_id, None)
        if a:
            a.chats.discard(chat_id)

    # ---------------- auto queue ----------------
    def _autofill(self, chat_id: int):
        """Auto queue: with autoplay ON, keep at least MUSIC_AUTO_MIN similar songs waiting."""
        st = self.state.get(chat_id)
        if (not self.is_auto(chat_id) or not st or not st.current or st.current.live
                or len(st.queue) >= MUSIC_AUTO_MIN or chat_id in self._filling):
            return
        self._filling.add(chat_id)

        async def _go():
            try:
                st2 = self.state.get(chat_id)
                if not st2 or not st2.current:
                    return
                base = st2.current
                exclude = set(st2.history) | {t.vid for t in st2.queue if t.vid}
                found = await related_tracks(base, exclude, limit=MUSIC_AUTO_BATCH * 3, user="Auto Queue")
                top = found[:MUSIC_AUTO_BATCH * 2]
                random.shuffle(top)                      # variety: not always the same first hits
                found = top + found[MUSIC_AUTO_BATCH * 2:]
                st2 = self.state.get(chat_id)
                if not st2 or not st2.current:
                    return
                added = 0
                for t in found:
                    if added >= MUSIC_AUTO_BATCH:
                        break
                    if any(self._same(t, q) for q in st2.queue) or self._same(t, st2.current):
                        continue
                    st2.queue.append(t)
                    added += 1
                if added:
                    self._warm_queue(st2)
                    log.info(f"♾ auto queue added {added} song(s) in {chat_id}")
            except Exception:
                log.warning("auto queue refill failed", exc_info=True)
            finally:
                self._filling.discard(chat_id)

        t = asyncio.create_task(_go())
        _bg_tasks.add(t)
        t.add_done_callback(_bg_tasks.discard)

    # ---------------- queue management (admin controls) ----------------
    async def shuffle(self, chat_id: int) -> int:
        async with self._lock(chat_id):
            st = self.state.get(chat_id)
            if not st or len(st.queue) < 2:
                return 0
            random.shuffle(st.queue)
            self._warm_queue(st)
            return len(st.queue)

    async def remove(self, chat_id: int, number: int) -> Optional[Track]:
        async with self._lock(chat_id):
            st = self.state.get(chat_id)
            if not st or not 1 <= number <= len(st.queue):
                return None
            t = st.queue.pop(number - 1)
            release(t, st.queue)
            return t

    async def clear_queue(self, chat_id: int) -> int:
        async with self._lock(chat_id):
            st = self.state.get(chat_id)
            if not st or not st.queue:
                return 0
            n = len(st.queue)
            for t in st.queue:
                release(t)
            st.queue.clear()
            return n

    async def set_volume(self, chat_id: int, volume: int) -> bool:
        st = self.state.get(chat_id)
        if not st or not st.current:
            return False
        await self._a(chat_id).calls.change_volume_call(chat_id, int(volume))
        st.volume = int(volume)
        return True

    async def set_mute(self, chat_id: int, mute: bool) -> bool:
        st = self.state.get(chat_id)
        if not st or not st.current or st.muted == mute:
            return False
        c = self._a(chat_id).calls
        await (c.mute(chat_id) if mute else c.unmute(chat_id))
        st.muted = mute
        return True

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
        task, track.thumb_task = track.thumb_task, None
        path = await task if task else await make_thumb(track)
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
        self._autofill(chat_id)              # fill the queue right away
        return True

    async def similar_tracks(self, chat_id: int, base: Optional[Track] = None, limit: int = 16) -> list:
        """Songs similar to `base` (default: the current track) for the picker."""
        st = self.state.get(chat_id)
        base = base or (st.current if st else None)
        if base and base.live:
            return []
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
        await self._a(chat_id).calls.pause(chat_id)
        st.offset, st.paused = float(pos), True
        return True

    async def resume(self, chat_id: int) -> bool:
        st = self.state.get(chat_id)
        if not st or not st.current or not st.paused:
            return False
        await self._a(chat_id).calls.resume(chat_id)
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
                await self._a(chat_id).calls.leave_call(chat_id)
            except Exception:
                pass
            self._unbind(chat_id)
            return had

    async def _say(self, chat_id: int, text: str):
        try:
            await self.bot.send_message(
                chat_id, text, parse_mode=enums.ParseMode.HTML
            )
        except Exception:
            pass


_bg_tasks: set = set()

music_player = MusicPlayer()
