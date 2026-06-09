import logging
from datetime import date

from telegram import Bot
from telegram.error import TelegramError

from config import BOT_TOKEN
from database import get_all_tracked_movies, mark_notification_sent, notification_sent
from tmdb_client import get_release_events

logger = logging.getLogger(__name__)

TODAY = date.today().isoformat()

_EVENT_LABELS = {
    "theatrical": "🎭 Theatrical release today!",
    "digital": "💻 Digital release today!",
    "physical": "💿 Physical/Blu-ray release today!",
}


async def _notify(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except TelegramError as e:
        logger.warning("Failed to notify user_id=%s: %s", user_id, e)


async def check_movies(bot: Bot) -> None:
    movies = get_all_tracked_movies()
    logger.info("Checking %d tracked movie records...", len(movies))

    for user_id, movie_id, movie_title in movies:
        try:
            events = get_release_events(movie_id)
            logger.debug("%s -> %s", movie_title, events)

            for event_type, event_date in events.items():
                if event_date != TODAY:
                    continue
                if notification_sent(user_id, movie_id, event_type):
                    continue

                label = _EVENT_LABELS.get(event_type, f"{event_type} release today!")
                message = f"🎬 {movie_title}\n\n{label}\n📅 {event_date}"

                await _notify(bot, user_id, message)
                mark_notification_sent(user_id, movie_id, event_type)
                logger.info("Notified user=%s: %s (%s)", user_id, movie_title, event_type)

        except Exception:
            logger.exception("Error checking movie_id=%s (%s)", movie_id, movie_title)


if __name__ == "__main__":
    import asyncio

    async def _main():
        bot = Bot(token=BOT_TOKEN)
        try:
            await check_movies(bot)
        finally:
            await bot.close()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )
    logger.info("Release Checker started (%s)", TODAY)
    asyncio.run(_main())
    logger.info("Done.")
