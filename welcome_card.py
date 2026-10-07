"""
welcome_card.py - generates the 1280x720 "WELCOME" card used by the welcome system.

    pip install pillow            (Pillow >= 10.1)

Fonts live in ./assets and MUST be committed to your repo (Render's disk is
wiped on every deploy):
    assets/DejaVuSans.ttf                   <- required (already included)
Optional, nicer look - if you add these they are used automatically:
    assets/Montserrat-ExtraBoldItalic.ttf   (title)
    assets/Montserrat-SemiBold.ttf          (info text)
    assets/Montserrat-Bold.ttf              (button text)

With only DejaVuSans.ttf the bold / italic looks are drawn by the code
(thicker strokes + a slant), so the card still looks right.

Usage:
    buf = generate_welcome(avatar, name, user_id, username)   # -> BytesIO (PNG)
`avatar` can be a file path, raw bytes, a BytesIO, or None (an initial-letter
placeholder is drawn instead).
"""
import io
import math
import os
import unicodedata

from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1280, 720
BG = (0, 0, 0)
CYAN = (79, 224, 238)
BLUE = (76, 125, 255)
LIME = (190, 245, 100)
WHITE = (255, 255, 255)
GREY = (165, 175, 185)

CREDIT = "ꞋꞋꞌꞋ𝚨ᴘє𝙭 ɴᴇᴛᴡᴏʀᴋ"

_HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(_HERE, "assets")

# Pillow renamed its resampling constants; support both spellings.
LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")

# Fallback search for the base font (first one that exists wins).
_BASE_FONT_CANDIDATES = [
    os.path.join(ASSETS, "DejaVuSans.ttf"),
    os.path.join(_HERE, "DejaVuSans.ttf"),
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]

# style -> (preferred font file, faux-bold stroke px, faux-italic)
# The preferred file is used when it exists; otherwise DejaVu is used and
# the stroke / italic are applied by hand.
_STYLES = {
    "title":  ("Montserrat-ExtraBoldItalic.ttf", 3, True),
    "info":   ("Montserrat-SemiBold.ttf", 1, False),
    "button": ("Montserrat-Bold.ttf", 1, False),
    "credit": (None, 0, False),
    "plain":  (None, 0, False),
}

_font_cache = {}
_notdef_cache = {}


def _base_font_path():
    for p in _BASE_FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _style(style, size):
    """-> (font, stroke_px, italic). Cached."""
    key = (style, size)
    if key in _font_cache:
        return _font_cache[key]
    preferred, stroke, italic = _STYLES[style]
    font = None
    if preferred:
        p = os.path.join(ASSETS, preferred)
        if os.path.exists(p):
            try:
                font = ImageFont.truetype(p, size)
                stroke, italic = 0, False      # real bold/italic font - no faking
            except OSError:
                font = None
    if font is None:
        base = _base_font_path()
        try:
            font = ImageFont.truetype(base, size) if base else ImageFont.load_default(size)
        except OSError:
            font = ImageFont.load_default(size)   # Pillow >= 10.1
    _font_cache[key] = (font, stroke, italic)
    return _font_cache[key]


# ---------------------------------------------------------------------------
# Text safety: fonts show an ugly empty box for characters they don't have
# (emoji, Hindi, CJK ...). Clean those out of the card text first.
# ---------------------------------------------------------------------------
def _glyph_sig(font, ch):
    """Pixels of `ch` drawn on a small blank image (version-proof way to
    compare glyphs - works on every Pillow release)."""
    img = Image.new("L", (72, 72), 0)
    ImageDraw.Draw(img).text((8, 8), ch, font=font, fill=255)
    return img.tobytes()


def _has_glyph(font, ch):
    nd = _notdef_cache.get(id(font))
    if nd is None:
        nd = _glyph_sig(font, "\uffff")             # guaranteed missing -> ".notdef" box
        _notdef_cache[id(font)] = nd
    return _glyph_sig(font, ch) != nd


def clean_text(text, limit=40):
    """Make `text` safe to draw: fancy letters -> plain ones where possible
    (NFKC), unsupported characters dropped, whitespace tidied, length capped."""
    font = _style("plain", 24)[0]
    out = []
    prev_dropped = True          # nothing kept yet: a leading combining mark has no base letter
    for ch in str(text or ""):
        cat = unicodedata.category(ch)
        if cat in ("Cc", "Cf", "Cs", "Co", "Cn") or 0xFE00 <= ord(ch) <= 0xFE0F:
            continue                                # control / format / variation selectors
        if cat in ("Mn", "Mc", "Me") and prev_dropped:
            continue                                # accent/vowel sign whose base letter was dropped
        if ch.isspace():
            out.append(" ")
            prev_dropped = False
        elif _has_glyph(font, ch):
            out.append(ch)
            prev_dropped = False
        else:
            kept = False
            for sub in unicodedata.normalize("NFKC", ch):
                if sub.isspace():
                    out.append(" ")
                    kept = True
                elif _has_glyph(font, sub):
                    out.append(sub)
                    kept = True
            prev_dropped = not kept
    s = " ".join("".join(out).split())
    if len(s) > limit:
        s = s[: limit - 1].rstrip() + "…"
    return s


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def _fit(draw, text, style, size, max_w):
    """Shrink the font until `text` fits max_w."""
    while size > 18:
        font, stroke, _ = _style(style, size)
        if draw.textlength(text, font=font) + 2 * stroke <= max_w:
            return size
        size -= 2
    return 18


def _text(canvas, xy, text, style, size, fill, anchor="la"):
    """Draw text in one of the card styles (handles faux bold / italic)."""
    font, stroke, italic = _style(style, size)
    if not italic:
        ImageDraw.Draw(canvas).text(xy, text, font=font, fill=fill, anchor=anchor,
                                    stroke_width=stroke, stroke_fill=fill)
        return
    # faux italic: draw upright on a small layer, shear it, paste (anchor "la" only)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=font, stroke_width=stroke)
    pad = 6
    lw, lh = r - l + 2 * pad, b - t + 2 * pad
    shear = 0.22
    layer = Image.new("L", (lw, lh), 0)
    ImageDraw.Draw(layer).text((pad - l, pad - t), text, font=font, fill=255,
                               stroke_width=stroke, stroke_fill=255)
    extra = int(lh * shear) + 2
    layer = layer.transform((lw + extra, lh), Image.AFFINE,
                            (1, shear, -shear * lh, 0, 1, 0), resample=Image.BICUBIC)
    colour = Image.new("RGB", layer.size, fill)
    canvas.paste(colour, (int(xy[0] + l - pad), int(xy[1] + t - pad)), layer)


def _dots(draw, cx, cy, start_r, end_r, step=22, color=CYAN):
    """Concentric dotted rings (corner decoration)."""
    r = start_r
    while r <= end_r:
        n = max(8, int(2 * math.pi * r / 14))
        size = max(1.2, 3.2 - (r - start_r) / 40)
        for i in range(n):
            a = 2 * math.pi * i / n
            x, y = cx + r * math.cos(a), cy + r * math.sin(a)
            draw.ellipse((x - size, y - size, x + size, y + size), fill=color)
        r += step


def _open_avatar(src):
    """path / bytes / file-like -> RGB image, or None if it can't be read."""
    if src is None:
        return None
    try:
        if isinstance(src, (bytes, bytearray)):
            src = io.BytesIO(src)
        elif isinstance(src, (str, os.PathLike)):
            if not os.path.exists(src):
                return None
        elif hasattr(src, "seek"):
            src.seek(0)
        img = Image.open(src)
        img = ImageOps.exif_transpose(img) or img
        return img.convert("RGB")
    except Exception:
        return None                                 # broken / non-image file -> placeholder


def _circle_avatar(src, size, initial="?"):
    img = _open_avatar(src)
    if img is None:                                 # no profile photo -> initial-letter placeholder
        img = Image.new("RGB", (size, size), (40, 44, 70))
        d = ImageDraw.Draw(img)
        font, stroke, _ = _style("info", size // 2)
        d.text((size / 2, size / 2), initial, font=font, fill=CYAN, anchor="mm",
               stroke_width=stroke, stroke_fill=CYAN)
    img = ImageOps.fit(img, (size, size), LANCZOS)
    s = 4                                           # supersample for a smooth edge
    mask = Image.new("L", (size * s, size * s), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size * s - 1, size * s - 1), fill=255)
    img.putalpha(mask.resize((size, size), LANCZOS))
    return img


# ---------------------------------------------------------------------------
# The card
# ---------------------------------------------------------------------------
def generate_welcome(avatar, name, user_id, username, out_path=None):
    """Returns a BytesIO holding the PNG. `avatar` may be None."""
    name = clean_text(name, 40) or "Member"
    username = clean_text(username, 40) if username else ""
    username = username or "None"
    user_id = str(user_id)

    canvas = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(canvas)

    # --- decorations ---
    d.ellipse((695, -90, 805, 50), fill=CYAN)            # top circle
    d.ellipse((930, 668, 1040, 780), fill=CYAN)          # bottom circle (nudged left: room for the credit)
    _dots(d, W, 0, 20, 160)                              # top-right dots
    _dots(d, 0, H, 20, 150)                              # bottom-left dots

    # --- title ---
    _text(canvas, (115, 40), "WELCOME", "title", 110, CYAN)

    # --- info lines ---
    max_w = 650
    for text, cy in ((f"NAME : {name}", 282), (f"ID : {user_id}", 373), (f"USERNAME : {username}", 463)):
        size = _fit(d, text, "info", 46, max_w)
        _text(canvas, (66, cy), text, "info", size, WHITE, anchor="lm")

    # --- avatar with rings (supersampled only around the avatar - cheap on memory) ---
    cx, cy, av_size = 985, 360, 400
    s = 4
    ring_r = av_size // 2 + 28
    arc_r = ring_r + 32
    half = arc_r + 8
    layer = Image.new("RGBA", (2 * half * s, 2 * half * s), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    c = half * s

    def circle(r, **kw):
        ld.ellipse((c - r * s, c - r * s, c + r * s, c + r * s), **kw)

    circle(ring_r, fill=CYAN)
    circle(av_size // 2 + 6, fill=BG + (255,))
    ld.arc((c - arc_r * s, c - arc_r * s, c + arc_r * s, c + arc_r * s),
           start=80, end=285, fill=LIME, width=4 * s)
    layer = layer.resize((2 * half, 2 * half), LANCZOS)
    canvas.paste(layer, (cx - half, cy - half), layer)

    av = _circle_avatar(avatar, av_size - 12, (name[:1] or "?").upper())
    canvas.paste(av, (cx - av.width // 2, cy - av.height // 2), av)

    # --- button ---
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((230, 633, 738, 702), radius=18, fill=BLUE)
    _text(canvas, (484, 668), "THANKS FOR JOINING", "button", 34, WHITE, anchor="mm")

    # --- copyright, bottom-right corner ---
    # (run through clean_text: DejaVu has no glyph for the two "math" letters in
    #  the credit, so they are swapped for the matching plain letters)
    credit = clean_text(CREDIT, 60)
    size = _fit(d, credit, "credit", 22, 215)
    _text(canvas, (W - 22, H - 16), credit, "credit", size, GREY, anchor="rs")

    buf = io.BytesIO()
    canvas.save(buf, "PNG", optimize=True)
    buf.seek(0)
    buf.name = "welcome.png"
    if out_path:
        canvas.save(out_path)
    return buf
