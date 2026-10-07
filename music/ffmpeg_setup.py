# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Music: make sure an ffmpeg binary is on PATH
# ============================================================
# Render's plain Python runtime has no ffmpeg. The imageio-ffmpeg wheel
# ships a static binary; we expose it as `ffmpeg` so py-tgcalls finds it.

import os
import shutil
import logging
import tempfile

log = logging.getLogger("music")


def ensure_ffmpeg() -> bool:
    if shutil.which("ffmpeg"):
        return True
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        bindir = os.path.join(tempfile.gettempdir(), "elina-bin")
        os.makedirs(bindir, exist_ok=True)
        link = os.path.join(bindir, "ffmpeg")
        if not os.path.exists(link):
            os.symlink(exe, link)
        os.environ["PATH"] = bindir + os.pathsep + os.environ.get("PATH", "")
        log.info("🎞 Using bundled ffmpeg")
        return bool(shutil.which("ffmpeg"))
    except Exception as e:
        log.warning(f"ffmpeg not available: {e}")
        return False
