# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: "now playing" thumbnail (Pillow only)
# ============================================================
# Frosted-glass card: blurred artwork background, rounded cover art,
# title, progress bar and player controls.
#
#   path = await make_thumb(track)      # -> png path, or None on failure
#   gen_thumb(src, title, duration, channel)   # sync version

import io
import os
import asyncio
import tempfile
import urllib.request

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .settings import MUSIC_BRAND

COPYRIGHT = MUSIC_BRAND
W, H = 1280, 720
_HERE = os.path.dirname(os.path.abspath(__file__))
_ASSETS = os.path.join(_HERE, "..", "assets")

_MAIN = [os.path.join(_HERE, "font.ttf"),
         os.path.join(_ASSETS, "DejaVuSans-Bold.ttf"),
         os.path.join(_ASSETS, "DejaVuSans.ttf"),
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "arial.ttf"]
_FANCY = [os.path.join(_HERE, "fancy.ttf"),
          "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"] + _MAIN


def _font(paths, size):
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _load(src):
    if os.path.exists(src):
        return Image.open(src).convert("RGB")
    req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGB")


def _cover(img, w, h, fy=0.5):
    r = max(w / img.width, h / img.height)
    img = img.resize((int(img.width * r) + 1, int(img.height * r) + 1), Image.LANCZOS)
    x = (img.width - w) // 2
    y = int((img.height - h) * fy)
    return img.crop((x, y, x + w, y + h))


def _mask(size, r):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), r, fill=255)
    return m


def _fit(d, text, size, max_w, paths=_MAIN):
    f = _font(paths, size)
    if d.textlength(text, font=f) <= max_w:
        return text, f
    while len(text) > 3 and d.textlength(text + "…", font=f) > max_w:
        text = text[:-1]
    return text + "…", f


def gen_thumb(src, title="Unknown", duration="0:00", channel="", played=0.0,
              out="thumb.png", focus_y=0.25):
    try:
        art = _load(src)
    except Exception:
        art = Image.new("RGB", (640, 640), (40, 30, 70))   # no artwork: plain card

    # soft blurred background
    bg = _cover(art, W, H, focus_y).filter(ImageFilter.GaussianBlur(40)).convert("RGBA")
    bg.alpha_composite(Image.new("RGBA", (W, H), (10, 8, 20, 90)))

    # frosted glass card
    cx0, cy0, cx1, cy1 = 90, 90, W - 90, H - 90
    cw, ch = cx1 - cx0, cy1 - cy0
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((cx0, cy0 + 14, cx1, cy1 + 14), 48, fill=(0, 0, 0, 120))
    bg.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(26)))

    glass = bg.crop((cx0, cy0, cx1, cy1)).filter(ImageFilter.GaussianBlur(12))
    glass.alpha_composite(Image.new("RGBA", glass.size, (255, 255, 255, 46)))
    bg.paste(glass, (cx0, cy0), _mask(glass.size, 48))
    ImageDraw.Draw(bg, "RGBA").rounded_rectangle((cx0, cy0, cx1, cy1), 48,
                                                 outline=(255, 255, 255, 90), width=2)

    # artwork (square, rounded) with soft shadow
    s = ch - 90
    ax, ay = cx0 + 45, cy0 + 45
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((ax, ay + 10, ax + s, ay + s + 10), 34, fill=(0, 0, 0, 130))
    bg.alpha_composite(sh.filter(ImageFilter.GaussianBlur(16)))
    a = _cover(art, s, s, focus_y).convert("RGBA")
    bg.paste(a, (ax, ay), _mask((s, s), 34))

    d = ImageDraw.Draw(bg, "RGBA")
    tx = ax + s + 55
    tw_max = cx1 - 55 - tx
    white, soft = (255, 255, 255, 255), (255, 255, 255, 170)

    d.text((tx, ay + 22), "N O W   P L A Y I N G", font=_font(_MAIN, 17), fill=soft)

    f1 = _font(_MAIN, 38)
    words, lines, cur = title.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f1) <= tw_max:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    if len(lines) > 2:
        lines = [lines[0], _fit(d, " ".join(lines[1:]), 38, tw_max)[0]]
    for i, ln in enumerate(lines):
        d.text((tx, ay + 62 + i * 50), ln, font=f1, fill=white)
    if channel:
        t2, f2 = _fit(d, channel, 24, tw_max)
        d.text((tx, ay + 62 + len(lines) * 50 + 8), t2, font=f2, fill=soft)

    # progress bar
    py = ay + 235
    d.rounded_rectangle((tx, py - 3, tx + tw_max, py + 3), 3, fill=(255, 255, 255, 80))
    kx = tx + int(tw_max * max(0, min(1, played)))
    d.rounded_rectangle((tx, py - 3, max(kx, tx + 6), py + 3), 3, fill=white)
    d.ellipse((kx - 9, py - 9, kx + 9, py + 9), fill=white)
    fs = _font(_MAIN, 18)
    d.text((tx, py + 16), "0:00", font=fs, fill=soft)
    d.text((tx + tw_max - d.textlength(duration, font=fs), py + 16), duration, font=fs, fill=soft)

    # controls: prev / play / next
    cy = py + 105
    mid = tx + tw_max // 2
    d.ellipse((mid - 36, cy - 36, mid + 36, cy + 36), fill=white)
    d.polygon([(mid - 10, cy - 18), (mid - 10, cy + 18), (mid + 20, cy)], fill=(30, 20, 50))
    x0 = mid - 110   # previous: |<
    d.polygon([(x0 - 14, cy), (x0 + 8, cy - 16), (x0 + 8, cy + 16)], fill=white)
    d.rectangle((x0 - 20, cy - 16, x0 - 16, cy + 16), fill=white)
    x1 = mid + 110   # next: >|
    d.polygon([(x1 + 14, cy), (x1 - 8, cy - 16), (x1 - 8, cy + 16)], fill=white)
    d.rectangle((x1 + 16, cy - 16, x1 + 20, cy + 16), fill=white)

    # brand (bottom-right corner, subtle)
    fc = _font(_FANCY, 22)
    cwid = d.textlength(COPYRIGHT, font=fc)
    d.text((W - 30 - cwid, H - 52), COPYRIGHT, font=fc, fill=(255, 255, 255, 215))

    bg.convert("RGB").save(out, quality=95)
    return out


async def make_thumb(track, played: float = 0.0):
    """Build the card for a Track in a worker thread. Returns the png path or None."""
    from .youtube import fmt_time
    src = track.thumb or (f"https://i.ytimg.com/vi/{track.vid}/hqdefault.jpg" if track.vid else "")
    fd, out = tempfile.mkstemp(prefix="elina_thumb_", suffix=".png")
    os.close(fd)
    try:
        await asyncio.to_thread(
            gen_thumb, src, track.title, fmt_time(track.duration), track.channel, played, out)
        return out
    except Exception:
        try:
            os.remove(out)
        except OSError:
            pass
        return None
