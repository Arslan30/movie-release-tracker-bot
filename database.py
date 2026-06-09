import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DB_NAME = "bot.db"


@contextmanager
def get_db():
    """Yield a WAL-mode connection; commit on success, rollback on error."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                movies  INTEGER DEFAULT 0,
                tv      INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS tv_notifications (
                user_id INTEGER,
                tv_id   INTEGER,
                season  INTEGER,
                episode INTEGER,
                PRIMARY KEY (user_id, tv_id, season, episode)
            );

            CREATE TABLE IF NOT EXISTS tracked_movies (
                user_id     INTEGER,
                movie_id    INTEGER,
                movie_title TEXT,
                PRIMARY KEY (user_id, movie_id)
            );

            CREATE TABLE IF NOT EXISTS tracked_tv (
                user_id  INTEGER,
                tv_id    INTEGER,
                tv_title TEXT,
                PRIMARY KEY (user_id, tv_id)
            );

            CREATE TABLE IF NOT EXISTS sent_notifications (
                user_id    INTEGER,
                movie_id   INTEGER,
                event_type TEXT,
                PRIMARY KEY (user_id, movie_id, event_type)
            );
        """)
    logger.info("Database initialised.")


# --------------------------------------------------
# Notification Tracking
# --------------------------------------------------

def notification_sent(user_id: int, movie_id: int, event_type: str) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_notifications "
            "WHERE user_id=? AND movie_id=? AND event_type=?",
            (user_id, movie_id, event_type),
        ).fetchone()
    return row is not None


def mark_notification_sent(user_id: int, movie_id: int, event_type: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO sent_notifications (user_id, movie_id, event_type) "
            "VALUES (?, ?, ?)",
            (user_id, movie_id, event_type),
        )


def notification_sent_tv(user_id: int, tv_id: int, season: int, episode: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM tv_notifications "
            "WHERE user_id=? AND tv_id=? AND season=? AND episode=?",
            (user_id, tv_id, season, episode),
        ).fetchone()
    return row is not None


def mark_notification_sent_tv(user_id: int, tv_id: int, season: int, episode: int) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO tv_notifications (user_id, tv_id, season, episode) "
            "VALUES (?, ?, ?, ?)",
            (user_id, tv_id, season, episode),
        )


# --------------------------------------------------
# Movie Tracking
# --------------------------------------------------

def track_movie(user_id: int, movie_id: int, movie_title: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO tracked_movies (user_id, movie_id, movie_title) "
            "VALUES (?, ?, ?)",
            (user_id, movie_id, movie_title),
        )


def untrack_movie(user_id: int, movie_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "DELETE FROM tracked_movies WHERE user_id=? AND movie_id=?",
            (user_id, movie_id),
        )


def is_movie_tracked(user_id: int, movie_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM tracked_movies WHERE user_id=? AND movie_id=?",
            (user_id, movie_id),
        ).fetchone()
    return row is not None


def get_tracked_movies(user_id: int) -> list[tuple]:
    with get_db() as conn:
        return conn.execute(
            "SELECT movie_id, movie_title FROM tracked_movies "
            "WHERE user_id=? ORDER BY movie_title",
            (user_id,),
        ).fetchall()


def get_all_tracked_movies() -> list[tuple]:
    with get_db() as conn:
        return conn.execute(
            "SELECT user_id, movie_id, movie_title FROM tracked_movies"
        ).fetchall()


# --------------------------------------------------
# TV Tracking
# --------------------------------------------------

def track_tv(user_id: int, tv_id: int, tv_title: str) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO tracked_tv (user_id, tv_id, tv_title) "
            "VALUES (?, ?, ?)",
            (user_id, tv_id, tv_title),
        )


def untrack_tv(user_id: int, tv_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "DELETE FROM tracked_tv WHERE user_id=? AND tv_id=?",
            (user_id, tv_id),
        )


def is_tv_tracked(user_id: int, tv_id: int) -> bool:
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM tracked_tv WHERE user_id=? AND tv_id=?",
            (user_id, tv_id),
        ).fetchone()
    return row is not None


def get_tracked_tv(user_id: int) -> list[tuple]:
    with get_db() as conn:
        return conn.execute(
            "SELECT tv_id, tv_title FROM tracked_tv "
            "WHERE user_id=? ORDER BY tv_title",
            (user_id,),
        ).fetchall()


def get_all_tracked_tv() -> list[tuple]:
    with get_db() as conn:
        return conn.execute(
            "SELECT user_id, tv_id, tv_title FROM tracked_tv"
        ).fetchall()


# --------------------------------------------------
# Subscribers
# --------------------------------------------------

def subscribe_movies(user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,)
        )
        conn.execute(
            "UPDATE subscribers SET movies=1 WHERE user_id=?", (user_id,)
        )


def unsubscribe_movies(user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE subscribers SET movies=0 WHERE user_id=?", (user_id,)
        )


def subscribe_tv(user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO subscribers (user_id) VALUES (?)", (user_id,)
        )
        conn.execute(
            "UPDATE subscribers SET tv=1 WHERE user_id=?", (user_id,)
        )


def unsubscribe_tv(user_id: int) -> None:
    with get_db() as conn:
        conn.execute(
            "UPDATE subscribers SET tv=0 WHERE user_id=?", (user_id,)
        )


def get_movie_subscribers() -> list[int]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT user_id FROM subscribers WHERE movies=1"
        ).fetchall()
    return [r[0] for r in rows]


def get_tv_subscribers() -> list[int]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT user_id FROM subscribers WHERE tv=1"
        ).fetchall()
    return [r[0] for r in rows]


def get_all_subscribers() -> list[tuple]:
    with get_db() as conn:
        return conn.execute("SELECT * FROM subscribers").fetchall()
