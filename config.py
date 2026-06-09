from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing from .env")

if not TMDB_API_KEY:
    raise ValueError("TMDB_API_KEY missing from .env")
