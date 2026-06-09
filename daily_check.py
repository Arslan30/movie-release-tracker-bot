"""
Daily notification runner.

Run via cron or systemd timer:
    0 9 * * * /path/to/venv/bin/python /path/to/daily_check.py

Or run manually:
    python daily_check.py
"""
import asyncio
import logging

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
    await check_movies()
    await check_tv_shows()
    logger.info("=== Daily check complete ===")


if __name__ == "__main__":
    asyncio.run(main())