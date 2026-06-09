import asyncio
import logging

from database import init_db          # add this
from release_checker import check_movies
from tv_checker import check_tv_shows

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("=== Daily check started ===")
    init_db()                          # add this
    await check_movies()
    await check_tv_shows()
    logger.info("=== Daily check complete ===")


if __name__ == "__main__":
    asyncio.run(main())