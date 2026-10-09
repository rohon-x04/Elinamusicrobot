# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: live radio (50+ stations)
# ============================================================
# * CURATED  : hand-picked internet radio streams (always available).
# * DYNAMIC  : the most popular working stations from radio-browser.info for the
#              countries in MUSIC_RADIO_COUNTRIES - tops the list up past 50 and
#              also powers  /radio <anything>  searches.
# * Dead streams are detected in the background at start-up and hidden.
#
# Check the curated list yourself any time:   python -m music.radio
# ============================================================

import asyncio
import logging
import re
import sys
import time
from dataclasses import dataclass

import httpx

log = logging.getLogger("music")

try:                                    # works as part of the bot AND as `python -m music.radio`
    from .settings import MUSIC_RADIO_COUNTRIES, MUSIC_RADIO_VALIDATE
except Exception:                       # pragma: no cover
    MUSIC_RADIO_COUNTRIES, MUSIC_RADIO_VALIDATE = ["IN", "US", "GB"], True


@dataclass
class Station:
    name: str
    url: str
    genre: str = ""
    country: str = ""
    logo: str = ""


def _soma(slug: str, name: str, genre: str) -> Station:
    return Station(f"SomaFM · {name}", f"https://ice1.somafm.com/{slug}-128-mp3", genre, "US")


CURATED: list = [
    # ---- SomaFM (listener-supported, commercial free) ----
    _soma("groovesalad", "Groove Salad", "Chill / Downtempo"),
    _soma("gsclassic", "Groove Salad Classic", "Chill / Downtempo"),
    _soma("dronezone", "Drone Zone", "Ambient"),
    _soma("deepspaceone", "Deep Space One", "Ambient"),
    _soma("spacestation", "Space Station", "Electronica"),
    _soma("secretagent", "Secret Agent", "Lounge"),
    _soma("lush", "Lush", "Vocal Chill"),
    _soma("defcon", "DEF CON Radio", "Hacker Beats"),
    _soma("beatblender", "Beat Blender", "Deep House"),
    _soma("thistle", "Thistle Radio", "Celtic"),
    _soma("bootliquor", "Boot Liquor", "Americana"),
    _soma("indiepop", "Indie Pop Rocks", "Indie Pop"),
    _soma("fluid", "Fluid", "Instrumental Hip-Hop"),
    _soma("illstreet", "Illinois Street Lounge", "Exotica / Lounge"),
    _soma("7soul", "Seven Inch Soul", "Vintage Soul"),
    _soma("poptron", "PopTron", "Synth Pop"),
    _soma("suburbsofgoa", "Suburbs of Goa", "Indian / World"),
    _soma("cliqhop", "cliqhop idm", "IDM"),
    _soma("dubstep", "Dub Step Beyond", "Dubstep"),
    _soma("folkfwd", "Folk Forward", "Folk"),
    _soma("missioncontrol", "Mission Control", "Space Ambient"),
    _soma("sonicuniverse", "Sonic Universe", "Jazz"),
    _soma("seventies", "Left Coast 70s", "70s"),
    _soma("covers", "Covers", "Cover Songs"),
    _soma("metal", "Metal Detector", "Metal"),
    _soma("reggae", "Heavyweight Reggae", "Reggae"),
    _soma("vaporwaves", "Vaporwaves", "Vaporwave"),
    _soma("u80s", "Underground 80s", "80s"),
    _soma("brfm", "Black Rock FM", "Eclectic"),
    _soma("thetrip", "The Trip", "Progressive House"),
    _soma("synphaera", "Synphaera", "Ambient"),
    _soma("sf1033", "SF 10-33", "Ambient / Scanner"),
    _soma("bagel", "BAGeL Radio", "Alternative"),
    _soma("digitalis", "Digitalis", "Indie Electronic"),
    _soma("n5md", "n5MD Radio", "Electronica"),
    # ---- Radio Paradise ----
    Station("Radio Paradise · Main Mix", "https://stream.radioparadise.com/mp3-192", "Eclectic", "US"),
    Station("Radio Paradise · Mellow Mix", "https://stream.radioparadise.com/mellow-192", "Mellow", "US"),
    Station("Radio Paradise · Rock Mix", "https://stream.radioparadise.com/rock-192", "Rock", "US"),
    Station("Radio Paradise · Global Mix", "https://stream.radioparadise.com/global-192", "World", "US"),
    # ---- Others ----
    Station("KEXP 90.3 Seattle", "https://kexp.streamguys1.com/kexp128.mp3", "Indie / Alternative", "US"),
    Station("BBC World Service", "https://stream.live.vc.bbcmedia.co.uk/bbc_world_service", "News", "GB"),
    Station("Chillhop Radio", "https://streams.fluxfm.de/Chillhop/mp3-320/audio/", "Lo-fi / Chillhop", "DE"),
    Station("I Love Radio", "https://streams.ilovemusic.de/iloveradio1.mp3", "Pop / Hits", "DE"),
    Station("I Love Dance", "https://streams.ilovemusic.de/iloveradio2.mp3", "Dance", "DE"),
    Station("I Love Hip Hop", "https://streams.ilovemusic.de/iloveradio3.mp3", "Hip-Hop", "DE"),
    Station("I Love Chill", "https://streams.ilovemusic.de/iloveradio10.mp3", "Chill", "DE"),
]

_catalog: list = []          # what /radio shows: validated curated + dynamic
_ready = False
_lock = asyncio.Lock()
_HOSTS = ["https://de1.api.radio-browser.info", "https://nl1.api.radio-browser.info",
          "https://at1.api.radio-browser.info"]
_UA = {"User-Agent": "ElinaMusicBot/2.0"}


def _dedupe(items) -> list:
    seen, out = set(), []
    for st in items:
        key = st.url.rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(st)
    return out


async def _rb(path: str, params: dict) -> list:
    """GET from radio-browser.info, trying the mirrors in turn. [] on failure."""
    async with httpx.AsyncClient(timeout=10, headers=_UA, follow_redirects=True) as c:
        for host in _HOSTS:
            try:
                r = await c.get(host + path, params=params)
                if r.status_code == 200:
                    return r.json() or []
            except Exception:
                continue
    return []


def _from_rb(row: dict) -> "Station | None":
    url = (row.get("url_resolved") or row.get("url") or "").strip()
    name = re.sub(r"\s+", " ", (row.get("name") or "").strip())
    if not url.startswith(("http://", "https://")) or not name:
        return None
    if url.lower().split("?")[0].endswith((".pls", ".m3u")):      # playlists, not streams
        return None
    return Station(name[:48], url, (row.get("tags") or "").split(",")[0].strip()[:24],
                   (row.get("countrycode") or "").upper(), row.get("favicon") or "")


async def search_online(query: str, limit: int = 8) -> list:
    """Stations matching a name/genre from radio-browser.info (working ones only)."""
    rows = await _rb("/json/stations/search", {
        "name": query, "limit": limit * 2, "hidebroken": "true", "order": "votes",
        "reverse": "true", "lastcheckok": 1})
    if not rows:
        rows = await _rb("/json/stations/search", {
            "tag": query, "limit": limit * 2, "hidebroken": "true", "order": "votes",
            "reverse": "true", "lastcheckok": 1})
    return _dedupe([s for s in map(_from_rb, rows) if s])[:limit]


async def _popular(country: str, limit: int = 25) -> list:
    rows = await _rb("/json/stations/search", {
        "countrycode": country, "limit": limit * 2, "hidebroken": "true",
        "order": "votes", "reverse": "true", "lastcheckok": 1})
    return [s for s in map(_from_rb, rows) if s][:limit]


async def alive(st: Station, timeout: float = 6.0) -> bool:
    """True when the stream answers and sends audio bytes."""
    try:
        async with httpx.AsyncClient(timeout=timeout, headers={**_UA, "Icy-MetaData": "0"},
                                     follow_redirects=True) as c:
            async with c.stream("GET", st.url) as r:
                if r.status_code != 200:
                    return False
                ctype = (r.headers.get("content-type") or "").lower()
                if "text/html" in ctype:
                    return False
                got = 0
                async for chunk in r.aiter_bytes(2048):
                    got += len(chunk)
                    if got >= 2048:
                        return True
                return got > 0
    except Exception:
        return False


async def _filter_alive(stations: list, parallel: int = 12) -> list:
    sem = asyncio.Semaphore(parallel)

    async def _one(st):
        async with sem:
            return st if await alive(st) else None

    res = await asyncio.gather(*[_one(s) for s in stations])
    return [s for s in res if s]


def stations() -> list:
    """The current list (curated until the background refresh has finished)."""
    return _catalog or _dedupe(CURATED)


async def refresh(validate: bool = None) -> int:
    """Rebuild the list: curated + popular stations of MUSIC_RADIO_COUNTRIES, dead ones removed."""
    global _catalog, _ready
    validate = MUSIC_RADIO_VALIDATE if validate is None else validate
    async with _lock:
        t0 = time.monotonic()
        base = _dedupe(CURATED)
        dyn = []
        for res in await asyncio.gather(*[_popular(c) for c in MUSIC_RADIO_COUNTRIES],
                                        return_exceptions=True):
            if isinstance(res, list):
                dyn += res
        merged = _dedupe(base + dyn)
        if validate:
            checked = await _filter_alive(merged)
            # never end up with a tiny list because the network was down while checking
            merged = checked if len(checked) >= 10 else merged
        _catalog, _ready = merged, True
        log.info("📻 radio list ready: %d stations (%.1fs)", len(_catalog), time.monotonic() - t0)
        return len(_catalog)


def start_background_refresh() -> None:
    t = asyncio.create_task(refresh())
    t.add_done_callback(lambda f: f.exception() and log.warning("radio refresh failed: %s", f.exception()))


def find_local(query: str) -> list:
    """Stations whose name or genre contains every word of the query."""
    words = [w for w in re.split(r"\W+", query.lower()) if w]
    out = []
    for st in stations():
        hay = f"{st.name} {st.genre} {st.country}".lower()
        if words and all(w in hay for w in words):
            out.append(st)
    return out


async def find(query: str) -> "Station | None":
    local = find_local(query)
    if local:
        return local[0]
    online = await search_online(query, limit=3)
    return online[0] if online else None


# ---- self-test:  python -m music.radio ------------------------------------------------
async def _selftest():
    items = _dedupe(CURATED)
    print(f"Checking {len(items)} curated stations ...")
    ok = await _filter_alive(items)
    dead = [s for s in items if s not in ok]
    print(f"\n✅ working: {len(ok)}")
    print(f"❌ not answering: {len(dead)}")
    for s in dead:
        print("   -", s.name, s.url)


if __name__ == "__main__":
    asyncio.run(_selftest())
    sys.exit(0)
