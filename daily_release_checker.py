from telegram import Bot

from config import BOT_TOKEN
from database import get_movie_subscribers
from tmdb_client import get_movies_today

bot = Bot(token=BOT_TOKEN)

movies = get_movies_today()

if movies:

    message = "Today's Movie Releases\n\n"

    for movie in movies[:20]:
        title = movie.get("title", "Unknown")
        message += f"• {title}\n"

    for user_id in get_movie_subscribers():
        bot.send_message(
            chat_id=user_id,
            text=message
        )