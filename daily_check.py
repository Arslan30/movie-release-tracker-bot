"""
Daily notification runner.
"""
import asyncio
import logging

from telegram import Bot

from config import BOT_TOKEN
from database import init_db
from release_checker import check_movies
from tv_checker import check_tv_shows

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("=== Daily check started ===")
    init_db()
    bot = Bot(token=BOT_TOKEN)
    try:
        await check_movies(bot)
        await check_tv_shows(bot)
    finally:
        await bot.close()
    logger.info("=== Daily check complete ===")


if __name__ == "__main__":
    asyncio.run(main())