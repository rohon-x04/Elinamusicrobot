"""
welcome_styles.py - picks a RANDOM welcome card for every new member.

    from welcome_styles import generate_random_welcome
    buf = generate_random_welcome(avatar, name, user_id, username)   # -> BytesIO

Styles in the draw:
  * "classic"  - the original cyan card from welcome_card.py
  * one "anime" card per picture you put in the  backgrounds/  folder
    (jpg / jpeg / png / webp). The picture is shown sharp on the right, a
    blurred copy fills the rest, and the accent colour is auto-detected from it.

Add more pictures to backgrounds/ = more variety. No pictures there = classic only.
Commit the pictures to your repo (Render's disk is wiped on every deploy).
"""
import colorsys
import glob
import io
import logging
import os
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageOps

import welcome_card as wc
from welcome_card import W, H, CREDIT, clean_text, _style, _open_avatar

log = logging.getLogger(__name__)

BG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backgrounds")
_EXT = (".jpg", ".jpeg", ".png", ".webp")
LANCZOS = wc.LANCZOS


# ---------------------------------------------------------------- helpers
def list_backgrounds():
    try:
        return sorted(p for p in glob.glob(os.path.join(BG_DIR, "*")) if p.lower().endswith(_EXT))
    except Exception:
        return []


def auto_accent(im):
    """Most vivid colour of the picture (used for lines / pill / glow)."""
    s = im.convert("RGB").resize((60, 60))
    best, tot = [0, 0, 0], 0
    for r, g, b in s.getdata():
        h, sa, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if sa > .45 and v > .55:
            best[0] += r; best[1] += g; best[2] += b; tot += 1
    if not tot:
        return (255, 255, 255)
    c = [best[i] / tot for i in range(3)]
    h, sa, v = colorsys.rgb_to_hsv(*[x / 255 for x in c])
    return tuple(int(x * 255) for x in colorsys.hsv_to_rgb(h, min(1, sa * 1.1), 1.0))


def _font(size, bold=False):
    font, stroke, _ = _style("title" if bold else "info", size)
    # faux-bold stroke scales with the text size (a fixed 3px blobs small text)
    return font, (max(1, round(size / 28)) if bold and stroke else (stroke if bold else 0))


def _txt(d, xy, text, size, fill, bold=False, anchor="la"):
    font, stroke = _font(size, bold)
    d.text(xy, text, font=font, fill=fill, anchor=anchor,
           stroke_width=max(stroke, 1 if bold else 0), stroke_fill=fill)


def _fit_size(d, text, size, max_w, bold=False):
    while size > 18:
        font, stroke = _font(size, bold)
        if d.textlength(text, font=font) + 2 * stroke <= max_w:
            return size
        size -= 2
    return 18


def glow_text(img, xy, text, size, fill, glow, radius=14):
    font, stroke = _font(size, True)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, text, font=font, fill=glow + (255,),
                               stroke_width=max(stroke, 1) + 2, stroke_fill=glow + (255,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(radius)))
    ImageDraw.Draw(img).text(xy, text, font=font, fill=fill, stroke_width=max(stroke, 1), stroke_fill=fill)


def speed_lines(img, cx, cy, color, n=50, width=5, length=380, alpha=28, seed=7):
    """Faint anime-style lines radiating from (cx, cy)."""
    import math
    rnd = random.Random(seed)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        a = rnd.uniform(0, 2 * math.pi)
        r1 = rnd.uniform(60, length)
        r2 = r1 + rnd.uniform(60, 220)
        d.line((cx + r1 * math.cos(a), cy + r1 * math.sin(a),
                cx + r2 * math.cos(a), cy + r2 * math.sin(a)),
               fill=color + (alpha,), width=rnd.randint(1, width))
    img.alpha_composite(layer)


def sparkles(img, color, n, seed, smin, smax, box):
    """Little 4-point stars scattered inside box = (x0, y0, x1, y1)."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y, s = rnd.randint(x0, x1), rnd.randint(y0, y1), rnd.randint(smin, smax)
        col = (255, 255, 255, 230) if rnd.random() < .5 else color + (230,)
        d.polygon([(x, y - s * 2), (x + s * .5, y - s * .5), (x + s * 2, y), (x + s * .5, y + s * .5),
                   (x, y + s * 2), (x - s * .5, y + s * .5), (x - s * 2, y), (x - s * .5, y - s * .5)], fill=col)
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(.6)))
    glow = layer.filter(ImageFilter.GaussianBlur(5))
    img.alpha_composite(glow)


def diamond_avatar(img, cx, cy, r, avatar, border, glow, initial="?"):
    """Avatar cropped to a diamond with a white border and a coloured glow."""
    R = int(r * 1.25)
    ss = 4
    size = 2 * R
    av = _open_avatar(avatar)
    if av is None:
        av = Image.new("RGB", (size, size), (40, 44, 70))
        f, st, _ = _style("info", size // 2)
        ImageDraw.Draw(av).text((size / 2, size / 2), initial, font=f, fill=glow, anchor="mm")
    av = ImageOps.fit(av, (size, size), LANCZOS).convert("RGBA")

    def poly(rad):
        c = size * ss // 2
        return [(c, c - rad * ss), (c + rad * ss, c), (c, c + rad * ss), (c - rad * ss, c)]

    big = Image.new("RGBA", (size * ss, size * ss), (0, 0, 0, 0))
    ImageDraw.Draw(big).polygon(poly(R), fill=border + (255,))             # border
    mask = Image.new("L", (size * ss, size * ss), 0)
    ImageDraw.Draw(mask).polygon(poly(R - 6), fill=255)                    # inner picture
    mask = mask.resize((size, size), LANCZOS)
    ring = big.resize((size, size), LANCZOS)
    halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
    halo.paste(ring, (cx - R, cy - R), ring)
    img.alpha_composite(halo.filter(ImageFilter.GaussianBlur(14)).point(lambda v: min(255, int(v * .9))))
    img.alpha_composite(halo)
    av.putalpha(mask)
    img.alpha_composite(av, (cx - R, cy - R))


def brand(img, color=(255, 255, 255)):
    d = ImageDraw.Draw(img)
    credit = clean_text(CREDIT, 60)
    size = _fit_size(d, credit, 22, 215)
    font, _ = _font(size)
    d.text((W - 22, H - 16), credit, font=font, fill=color + (200,), anchor="rs")


# ---------------------------------------------------------------- anime card
def make_bg_banner(bg_path, name, uid, username, avatar, accent=None, art_w=None, art_y=0):
    art = Image.open(bg_path).convert("RGB")
    acc = accent or auto_accent(art)
    s = max(W / art.width, H / art.height)
    big = art.resize((int(art.width * s) + 1, int(art.height * s) + 1), LANCZOS)
    l, t = (big.width - W) // 2, (big.height - H) // 2
    base = big.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(28))
    base = ImageEnhance.Brightness(base).enhance(.45).convert("RGBA")

    aw = art_w or int(art.width * H / art.height)
    aw = min(aw, int(W * .75))
    ah = int(art.height * aw / art.width)
    a = art.resize((aw, ah), LANCZOS).convert("RGBA")
    x0 = W - aw
    y0 = min(0, max(H - ah, art_y))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.paste(a, (x0, y0))
    fade = Image.new("L", (W, H), 255)
    fd = ImageDraw.Draw(fade)
    for i in range(140):
        fd.line((x0 + i, 0, x0 + i, H), fill=int(255 * i / 140))
    fd.rectangle((0, 0, x0, H), fill=0)
    layer.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", (W, H), 0), fade))
    base.alpha_composite(layer)

    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    for x in range(0, 760):
        sd.line((x, 0, x, H), fill=(0, 0, 0, int(170 * (1 - x / 760))))
    base.alpha_composite(sh)

    speed_lines(base, 330, 360, acc, 50, 5, 380, 28)
    sparkles(base, acc, 16, 3, 5, 13, (0, 0, W // 2 + 100, H))
    img = base
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((22, 22, W - 22, H - 22), 26, outline=acc + (120,), width=2)
    diamond_avatar(img, 150, 150, 72, avatar, (255, 255, 255), acc, (name[:1] or "?").upper())
    d = ImageDraw.Draw(img)
    glow_text(img, (262, 118), "WELCOME", 84, (255, 255, 255), acc, 14)
    d.rounded_rectangle((264, 218, 560, 223), 3, fill=acc + (255,))

    y = 300
    for k, v in (("NAME", name), ("ID", str(uid)), ("USERNAME", username)):
        _txt(d, (72, y), k, 20, acc + (255,), anchor="ls")
        _txt(d, (72, y + 40), v, _fit_size(d, v, 38, 560), (255, 255, 255, 255), anchor="ls")
        y += 90
    label = "THANKS FOR JOINING"
    pf, _ = _font(25, True)
    tw = d.textlength(label, font=pf)
    d.rounded_rectangle((72, y + 16, 72 + tw + 64, y + 72), 28, fill=acc + (255,))
    lum = .299 * acc[0] + .587 * acc[1] + .114 * acc[2]
    _txt(d, (72 + (tw + 64) / 2, y + 44), label, 25,
         (20, 10, 30, 255) if lum > 150 else (255, 255, 255, 255), bold=True, anchor="mm")
    brand(img, (255, 255, 255))
    return img.convert("RGB")


# ---------------------------------------------------------------- the picker
def generate_random_welcome(avatar, name, user_id, username, out_path=None):
    """Random card. Returns a BytesIO (PNG for classic, JPEG for the anime cards)."""
    bgs = list_backgrounds()
    choices = ["classic"] + bgs
    pick = random.choice(choices)
    if pick != "classic":
        try:
            nm = clean_text(name, 40) or "Member"
            un = (clean_text(username, 40) if username else "") or "None"
            img = make_bg_banner(pick, nm, user_id, un, avatar)
            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=92)
            buf.seek(0)
            buf.name = "welcome.jpg"
            if out_path:
                img.save(out_path)
            return buf
        except Exception:
            log.warning("Anime welcome card failed (%s) - using classic", pick, exc_info=True)
    return wc.generate_welcome(avatar, name, user_id, username, out_path)


# keep the old name working: `from welcome_styles import generate_welcome`
generate_welcome = generate_random_welcome
