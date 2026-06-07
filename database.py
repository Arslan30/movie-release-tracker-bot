import sqlite3

DB_NAME = "bot.db"


def init_db():

    conn = sqlite3.connect(DB_NAME)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id INTEGER PRIMARY KEY,
            movies INTEGER DEFAULT 0,
            tv INTEGER DEFAULT 0
        )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS tv_notifications (
        user_id INTEGER,
        tv_id INTEGER,
        season INTEGER,
        episode INTEGER,
        PRIMARY KEY(
            user_id,
            tv_id,
            season,
            episode
        )
    )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracked_movies (
            user_id INTEGER,
            movie_id INTEGER,
            movie_title TEXT,
            PRIMARY KEY(user_id, movie_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracked_tv (
            user_id INTEGER,
            tv_id INTEGER,
            tv_title TEXT,
            PRIMARY KEY(user_id, tv_id)
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS sent_notifications (
            user_id INTEGER,
            movie_id INTEGER,
            event_type TEXT,
            PRIMARY KEY(
                user_id,
                movie_id,
                event_type
            )
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# Notification Tracking
# --------------------------------------------------

def notification_sent(
    user_id,
    movie_id,
    event_type
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT 1
        FROM sent_notifications
        WHERE user_id = ?
        AND movie_id = ?
        AND event_type = ?
        """,
        (
            user_id,
            movie_id,
            event_type
        )
    )

    exists = (
        cursor.fetchone()
        is not None
    )

    conn.close()

    return exists

def notification_sent_tv(
    user_id,
    tv_id,
    season,
    episode
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT 1
        FROM tv_notifications
        WHERE user_id = ?
        AND tv_id = ?
        AND season = ?
        AND episode = ?
        """,
        (
            user_id,
            tv_id,
            season,
            episode
        )
    )

    exists = (
        cursor.fetchone()
        is not None
    )

    conn.close()

    return exists

def mark_notification_sent_tv(
    user_id,
    tv_id,
    season,
    episode
):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT OR IGNORE
        INTO tv_notifications
        (
            user_id,
            tv_id,
            season,
            episode
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            tv_id,
            season,
            episode
        )
    )

    conn.commit()
    conn.close()


def mark_notification_sent(
    user_id,
    movie_id,
    event_type
):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT OR IGNORE
        INTO sent_notifications
        (
            user_id,
            movie_id,
            event_type
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            movie_id,
            event_type
        )
    )

    conn.commit()
    conn.close()


# --------------------------------------------------
# Movie Tracking
# --------------------------------------------------

def track_movie(
    user_id,
    movie_id,
    movie_title
):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT OR IGNORE
        INTO tracked_movies
        (
            user_id,
            movie_id,
            movie_title
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            movie_id,
            movie_title
        )
    )

    conn.commit()
    conn.close()


def untrack_movie(
    user_id,
    movie_id
):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        DELETE FROM tracked_movies
        WHERE user_id = ?
        AND movie_id = ?
        """,
        (
            user_id,
            movie_id
        )
    )

    conn.commit()
    conn.close()


def is_movie_tracked(
    user_id,
    movie_id
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT 1
        FROM tracked_movies
        WHERE user_id = ?
        AND movie_id = ?
        """,
        (
            user_id,
            movie_id
        )
    )

    tracked = (
        cursor.fetchone()
        is not None
    )

    conn.close()

    return tracked


def get_tracked_movies(
    user_id
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT
            movie_id,
            movie_title
        FROM tracked_movies
        WHERE user_id = ?
        ORDER BY movie_title
        """,
        (user_id,)
    )

    movies = cursor.fetchall()

    conn.close()

    return movies


def get_all_tracked_movies():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT
            user_id,
            movie_id,
            movie_title
        FROM tracked_movies
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# --------------------------------------------------
# TV Tracking
# --------------------------------------------------
def get_all_tracked_tv():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT
            user_id,
            tv_id,
            tv_title
        FROM tracked_tv
        """
    )

    rows = cursor.fetchall()

    conn.close()

    return rows

def track_tv(
    user_id,
    tv_id,
    tv_title
):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT OR IGNORE
        INTO tracked_tv
        (
            user_id,
            tv_id,
            tv_title
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            tv_id,
            tv_title
        )
    )

    conn.commit()
    conn.close()


def untrack_tv(
    user_id,
    tv_id
):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        DELETE FROM tracked_tv
        WHERE user_id = ?
        AND tv_id = ?
        """,
        (
            user_id,
            tv_id
        )
    )

    conn.commit()
    conn.close()


def is_tv_tracked(
    user_id,
    tv_id
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT 1
        FROM tracked_tv
        WHERE user_id = ?
        AND tv_id = ?
        """,
        (
            user_id,
            tv_id
        )
    )

    tracked = (
        cursor.fetchone()
        is not None
    )

    conn.close()

    return tracked


def get_tracked_tv(
    user_id
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT
            tv_id,
            tv_title
        FROM tracked_tv
        WHERE user_id = ?
        ORDER BY tv_title
        """,
        (user_id,)
    )

    shows = cursor.fetchall()

    conn.close()

    return shows


# --------------------------------------------------
# Subscribers
# --------------------------------------------------

def subscribe_movies(user_id):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT OR IGNORE
        INTO subscribers(user_id)
        VALUES(?)
        """,
        (user_id,)
    )

    conn.execute(
        """
        UPDATE subscribers
        SET movies = 1
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def unsubscribe_movies(user_id):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        UPDATE subscribers
        SET movies = 0
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def subscribe_tv(user_id):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        INSERT OR IGNORE
        INTO subscribers(user_id)
        VALUES(?)
        """,
        (user_id,)
    )

    conn.execute(
        """
        UPDATE subscribers
        SET tv = 1
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def unsubscribe_tv(user_id):

    conn = sqlite3.connect(DB_NAME)

    conn.execute(
        """
        UPDATE subscribers
        SET tv = 0
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()
    conn.close()


def get_movie_subscribers():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT user_id
        FROM subscribers
        WHERE movies = 1
        """
    )

    users = [
        row[0]
        for row in cursor.fetchall()
    ]

    conn.close()

    return users


def get_tv_subscribers():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT user_id
        FROM subscribers
        WHERE tv = 1
        """
    )

    users = [
        row[0]
        for row in cursor.fetchall()
    ]

    conn.close()

    return users


def get_all_subscribers():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.execute(
        """
        SELECT *
        FROM subscribers
        """
    )

    users = cursor.fetchall()

    conn.close()

    return users