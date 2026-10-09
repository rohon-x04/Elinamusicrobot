# ᴇʟɪɴᴀ ꭙ ᴍᴜsɪᴄ˼ ♪

Telegram voice-chat music bot - **crystal clear Opus audio, lightning-fast playback**.

⚡ **Features**
- Crystal-clear audio: 320 kbps source -> 48 kHz stereo -> Telegram's Opus voice-chat encoder
- Lightning-fast playback: songs stream live from the API the moment they're found (no download wait),
  searches run together with the assistant joining, results are cached, queued songs are pre-downloaded
- Live radio: 50+ stations (`/radio`, `/radio bollywood`) - list is checked at start-up, dead streams hidden
- Smart queue: 50 songs, paged `/queue`, no duplicates, `/shuffle` `/remove` `/clear` `/playnext`
- Advanced admin controls: `/auth` `/unauth` `/authusers` `/playmode` `/skipmode` `/volume` `/mute` `/seek`
- Multi-assistants: add as many assistant accounts as you like (`/setstring`), groups are spread across them
- Song cache: every song is downloaded once, saved to Firebase and replayed from there (`/cache` for stats)
- Auto queue: `/autoplay` keeps the queue topped up with similar songs

**Music:** /play /vplay /playnext /radio /pause /resume /skip /end /queue /shuffle /remove /clear
/loop /np /autoplay /seek /volume /mute /unmute /favs /playfav
**Admin:** /auth /unauth /authusers /playmode /skipmode
**Owner (DM):** /setstring /assistants /delstring [n]
**Welcome:** sent automatically to new members (admins: /welcome, /setwelcome, /resetwelcome, /welcomecard)

Setup: copy `env.example` to `.env`, fill it in, `pip install -r requirements.txt`, `python3 main.py`.
Add the bot AND the assistant account(s) to your group, then start a voice chat.
More assistants: `STRING_SESSION2=...`, `STRING_SESSION3=...` (or `STRING_SESSIONS=a,b,c`) or `/setstring` in DM.
Check the radio list any time: `python -m music.radio`.
