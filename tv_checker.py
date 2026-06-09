import logging
from datetime import date

from telegram import Bot
from telegram.error import TelegramError

from config import BOT_TOKEN
from database import (
    get_all_tracked_tv,
    mark_notification_sent_tv,
    notification_sent_tv,
)
from tmdb_client import get_tv_details

logger = logging.getLogger(__name__)

TODAY = date.today().isoformat()


async def _notify(bot: Bot, user_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id=user_id, text=text)
    except TelegramError as e:
        logger.warning("Failed to notify user_id=%s: %s", user_id, e)


async def check_tv_shows(bot: Bot) -> None:
    shows = get_all_tracked_tv()
    logger.info("Checking %d tracked TV records...", len(shows))

    for user_id, tv_id, tv_title in shows:
        try:
            details = get_tv_details(tv_id)
            next_ep = details.get("next_episode_to_air")

            if not next_ep:
                logger.debug("%s -> no upcoming episode", tv_title)
                continue

            air_date = next_ep.get("air_date", "")
            season = next_ep.get("season_number")
            episode = next_ep.get("episode_number")

            logger.debug("%s -> S%sE%s (%s)", tv_title, season, episode, air_date)

            if air_date != TODAY:
                continue
            if notification_sent_tv(user_id, tv_id, season, episode):
                continue

            message = (
                f"📺 {tv_title}\n\n"
                f"New episode out today!\n"
                f"Season {season}, Episode {episode}\n"
                f"📅 {air_date}"
            )
            await _notify(bot, user_id, message)
            mark_notification_sent_tv(user_id, tv_id, season, episode)
            logger.info("Notified user=%s: %s S%sE%s", user_id, tv_title, season, episode)

        except Exception:
            logger.exception("Error checking tv_id=%s (%s)", tv_id, tv_title)


if __name__ == "__main__":
    import asyncio

    async def _main():
        bot = Bot(token=BOT_TOKEN)
        try:
            await check_tv_shows(bot)
        finally:
            await bot.close()

    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=logging.INFO,
    )
    logger.info("TV Checker started (%s)", TODAY)
    asyncio.run(_main())
    logger.info("Done.")
