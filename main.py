# ============================================================
# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ - Telegram voice-chat music bot
# Features: voice-chat music + welcome message. Nothing else.
# ============================================================

import asyncio

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import os
import logging
import threading
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

print("🚀 Starting ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪ ...")

for key in ("API_ID", "API_HASH", "BOT_TOKEN", "MUSIC_API_KEY"):
    print(f"{key}:", "SET" if os.getenv(key) else "❌ MISSING")

# Render "Web Service" deploys need an open HTTP port (health check only).
PORT = int(os.environ.get("PORT", 10000))


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Elina Music is running")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def start_web_server():
    try:
        server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
        logging.info(f"🌐 Health server running on port {PORT}")
        server.serve_forever()
    except Exception as e:
        print("❌ WEB SERVER ERROR:", e)
        traceback.print_exc()


threading.Thread(target=start_web_server, daemon=True).start()

try:
    from pyrogram import Client
    from config import API_ID, API_HASH, BOT_TOKEN
    from handlers import register_all_handlers

    app = Client("elina_music", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    register_all_handlers(app)

    from music import run_with_music   # voice-chat music (needs STRING_SESSION)

    run_with_music(app)                # replaces app.run()
    print("🛑 Bot stopped")

except Exception as e:
    print("💥 BOT CRASHED:", e)
    traceback.print_exc()
