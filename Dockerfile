# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - runtime image
#   docker build -t elina-music .
#   docker run -d --name elina --env-file .env -p 10000:10000 --restart unless-stopped elina-music
# ============================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=10000

# ffmpeg = the audio/video engine used by py-tgcalls (system build: faster + more codecs
# than the bundled one). The rest are build tools for the crypto wheels and fonts for thumbnails.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg ca-certificates curl gcc build-essential libffi-dev libssl-dev fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# dependencies first (cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install -U -r requirements.txt

COPY . .

# non-root user; downloads/ is where songs are cached while they play
RUN useradd -m -u 1000 elina \
 && mkdir -p /app/downloads \
 && chown -R elina:elina /app
USER elina

EXPOSE 10000

# main.py serves "Elina Music is running" on $PORT
HEALTHCHECK --interval=60s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/ || exit 1

CMD ["python3", "main.py"]
