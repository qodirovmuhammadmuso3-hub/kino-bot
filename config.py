import os
from dotenv import load_dotenv

load_dotenv()

def parse_channel(channel_str):
    """'id|link' yoki '@username|link' formatini parse qiladi."""
    if not channel_str or "|" not in channel_str:
        return {"id": channel_str, "link": f"https://t.me/{channel_str.replace('@', '')}" if channel_str else None}
    parts = channel_str.split("|")
    return {"id": parts[0].strip(), "link": parts[1].strip()}

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Majburiy kanallar ro'yxati (id|link formatida)
raw_channels = os.getenv("REQUIRED_CHANNELS", "").split(",")
REQUIRED_CHANNELS = [parse_channel(ch.strip()) for ch in raw_channels if ch.strip()]

DATABASE_URL = os.getenv("DATABASE_URL")
DB_NAME = os.getenv("DB_NAME", "postgres")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

TRAILER_CH_DATA = parse_channel(os.getenv("TRAILER_CHANNEL", ""))
TRAILER_CHANNEL = TRAILER_CH_DATA["id"]

MOVIE_CH_DATA = parse_channel(os.getenv("MOVIE_CHANNEL", ""))
MOVIE_CHANNEL = MOVIE_CH_DATA["id"]
