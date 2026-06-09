import logging
import time
from datetime import date

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN
from database import (
    get_tracked_movies,
    get_tracked_tv,
    init_db,
    is_movie_tracked,
    is_tv_tracked,
    subscribe_movies,
    subscribe_tv,
    track_movie,
    track_tv,
    unsubscribe_movies,
    unsubscribe_tv,
    untrack_movie,
    untrack_tv,
)
from tmdb_client import (
    get_movie_details,
    get_movies_by_date,
    get_movies_today,
    get_next_episode_info,
    get_poster_url,
    get_release_events,
    get_tv_details,
    search_movies,
    search_tv,
)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# In-memory search result cache with TTL
# --------------------------------------------------

_CACHE_TTL = 600  # seconds


class _TTLCache:
    def __init__(self, ttl: int = _CACHE_TTL):
        self._ttl = ttl
        self._store: dict[int, tuple[list, float]] = {}

    def set(self, user_id: int, results: list) -> None:
        self._store[user_id] = (results, time.monotonic())

    def get(self, user_id: int) -> list | None:
        entry = self._store.get(user_id)
        if entry is None:
            return None
        results, ts = entry
        if time.monotonic() - ts > self._ttl:
            del self._store[user_id]
            return None
        return results

    def clear_expired(self) -> None:
        now = time.monotonic()
        expired = [uid for uid, (_, ts) in self._store.items() if now - ts > self._ttl]
        for uid in expired:
            del self._store[uid]


movie_cache = _TTLCache()
tv_cache = _TTLCache()


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _days_label(target_date: str, today: date) -> str:
    try:
        delta = (date.fromisoformat(target_date) - today).days
        return f"{delta} days" if delta >= 0 else "Released"
    except ValueError:
        return "Unknown"


async def _send_movie_detail(query, movie: dict) -> None:
    movie_id = movie["id"]
    details = get_movie_details(movie_id)
    events = get_release_events(movie_id)

    title = details.get("title", "Unknown")
    rating = details.get("vote_average", "N/A")
    vote_count = details.get("vote_count", 0)
    overview = details.get("overview", "No overview available.")
    runtime = details.get("runtime", "?")
    status = details.get("status", "Unknown")
    release_date = details.get("release_date", "")
    year = release_date[:4] if release_date else "?"
    genres = ", ".join(g["name"] for g in details.get("genres", [])) or "Unknown"

    theatrical = events.get("theatrical", "Not announced")
    digital = events.get("digital", "Not announced")
    physical = events.get("physical", "Not announced")

    text = (
        f"🎬 {title} ({year})\n\n"
        f"⭐ Rating: {rating} ({vote_count:,} votes)\n"
        f"⏱ Runtime: {runtime} min\n"
        f"📡 Status: {status}\n"
        f"🏷 Genres: {genres}\n\n"
        f"🎭 Theatrical: {theatrical}\n"
        f"💻 Digital: {digital}\n"
        f"💿 Physical/Blu-ray: {physical}\n\n"
        f"{overview[:700]}"
    )

    poster_url = get_poster_url(details.get("poster_path"))
    if poster_url:
        await query.message.reply_photo(photo=poster_url, caption=text)
    else:
        await query.message.reply_text(text)


async def _send_tv_detail(query, show: dict) -> None:
    tv_id = show["id"]
    details = get_tv_details(tv_id)

    name = details.get("name", "Unknown")
    rating = details.get("vote_average", "N/A")
    vote_count = details.get("vote_count", 0)
    overview = details.get("overview", "No overview available.")
    status = details.get("status", "Unknown")
    first_air = details.get("first_air_date", "")
    last_air = details.get("last_air_date", "")
    seasons = details.get("number_of_seasons", "?")
    episodes = details.get("number_of_episodes", "?")
    genres = ", ".join(g["name"] for g in details.get("genres", [])) or "Unknown"
    year = first_air[:4] if first_air else "?"

    next_ep = details.get("next_episode_to_air")
    if next_ep:
        s = next_ep.get("season_number", "?")
        e = next_ep.get("episode_number", "?")
        air = next_ep.get("air_date", "Unknown")
        next_ep_text = f"📺 Next: S{s}E{e} — {air}\n\n"
    else:
        next_ep_text = "📺 Next: No upcoming episode\n\n"

    text = (
        f"📺 {name} ({year})\n\n"
        f"⭐ Rating: {rating} ({vote_count:,} votes)\n"
        f"📡 Status: {status}\n"
        f"🎞 Seasons: {seasons}  🎬 Episodes: {episodes}\n"
        f"🏷 Genres: {genres}\n\n"
        f"📅 First: {first_air}  Last: {last_air}\n\n"
        f"{next_ep_text}"
        f"{overview[:700]}"
    )

    poster_url = get_poster_url(details.get("poster_path"))
    if poster_url:
        await query.message.reply_photo(photo=poster_url, caption=text)
    else:
        await query.message.reply_text(text)


# --------------------------------------------------
# Command Handlers
# --------------------------------------------------

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎬 Movie Release Tracker\n\n"
        "/search <title>          — Search movies\n"
        "/searchtv <title>        — Search TV shows\n"
        "/mymovies                — Tracked movies\n"
        "/myshows                 — Tracked TV shows\n"
        "/comingsoon              — Upcoming movie releases\n"
        "/upcomingshows           — Upcoming TV episodes\n"
        "/today                   — Movies releasing today\n"
        "/date YYYY-MM-DD         — Movies on a specific date\n"
        "/subscribe_movies        — Enable movie notifications\n"
        "/unsubscribe_movies      — Disable movie notifications\n"
        "/subscribe_tv            — Enable TV notifications\n"
        "/unsubscribe_tv          — Disable TV notifications\n"
        "/ping                    — Health check"
    )


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Pong!")


async def cmd_today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    movies = get_movies_today()
    if not movies:
        await update.message.reply_text("No releases found for today.")
        return
    lines = [f"• {m.get('title', 'Unknown')} ⭐ {m.get('vote_average', 'N/A')}" for m in movies[:20]]
    await update.message.reply_text("🎬 Today's Releases\n\n" + "\n".join(lines))


async def cmd_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /date YYYY-MM-DD")
        return
    release_date = context.args[0]
    try:
        date.fromisoformat(release_date)
    except ValueError:
        await update.message.reply_text("Invalid date format. Use YYYY-MM-DD.")
        return

    movies = get_movies_by_date(release_date)
    if not movies:
        await update.message.reply_text(f"No releases found for {release_date}.")
        return

    lines = [
        f"• {m.get('title', 'Unknown')} ({(m.get('release_date') or '')[:4] or '?'}) "
        f"⭐ {m.get('vote_average', 'N/A')}"
        for m in movies[:20]
    ]
    await update.message.reply_text(f"🎬 Releases on {release_date}\n\n" + "\n".join(lines))


async def cmd_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /search <movie title>")
        return

    query = " ".join(context.args)
    results = search_movies(query)
    if not results:
        await update.message.reply_text(f"No results found for '{query}'.")
        return

    user_id = update.effective_user.id
    results = results[:10]
    movie_cache.set(user_id, results)

    for i, movie in enumerate(results):
        title = movie.get("title", "Unknown")
        rating = movie.get("vote_average", "N/A")
        year = (movie.get("release_date") or "")[:4] or "?"
        movie_id = movie["id"]

        track_btn = (
            InlineKeyboardButton("Tracked ✓", callback_data="tracked")
            if is_movie_tracked(user_id, movie_id)
            else InlineKeyboardButton("Track", callback_data=f"track:{i}")
        )
        keyboard = [[InlineKeyboardButton("Details", callback_data=f"details:{i}"), track_btn]]
        await update.message.reply_text(
            f"🎬 {title} ({year})  ⭐ {rating}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def cmd_searchtv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /searchtv <show title>")
        return

    query = " ".join(context.args)
    results = search_tv(query)
    if not results:
        await update.message.reply_text(f"No results found for '{query}'.")
        return

    user_id = update.effective_user.id
    results = results[:10]
    tv_cache.set(user_id, results)

    for i, show in enumerate(results):
        name = show.get("name", "Unknown")
        rating = show.get("vote_average", "N/A")
        year = (show.get("first_air_date") or "")[:4] or "?"
        tv_id = show["id"]

        track_btn = (
            InlineKeyboardButton("Tracked ✓", callback_data="tvtracked")
            if is_tv_tracked(user_id, tv_id)
            else InlineKeyboardButton("Track", callback_data=f"tvtrack:{i}")
        )
        keyboard = [[InlineKeyboardButton("Details", callback_data=f"tvdetails:{i}"), track_btn]]
        await update.message.reply_text(
            f"📺 {name} ({year})  ⭐ {rating}",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


async def cmd_mymovies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    movies = get_tracked_movies(user_id)
    if not movies:
        await update.message.reply_text("You are not tracking any movies.")
        return
    for movie_id, movie_title in movies:
        keyboard = [[InlineKeyboardButton("Untrack", callback_data=f"untrack:{movie_id}")]]
        await update.message.reply_text(movie_title, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_myshows(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    shows = get_tracked_tv(user_id)
    if not shows:
        await update.message.reply_text("You are not tracking any TV shows.")
        return
    for tv_id, tv_title in shows:
        keyboard = [[InlineKeyboardButton("Untrack", callback_data=f"untracktv:{tv_id}")]]
        await update.message.reply_text(tv_title, reply_markup=InlineKeyboardMarkup(keyboard))


async def cmd_comingsoon(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    movies = get_tracked_movies(user_id)
    if not movies:
        await update.message.reply_text("You are not tracking any movies.")
        return

    today = date.today()
    await update.message.reply_text(f"🎬 Upcoming Releases ({len(movies)} tracked)")

    for movie_id, movie_title in movies:
        try:
            events = get_release_events(movie_id)
            theatrical = events.get("theatrical")
            digital = events.get("digital", "Not announced")
            physical = events.get("physical", "Not announced")

            countdown = _days_label(theatrical, today) if theatrical else "Unknown"
            theatrical_str = theatrical or "Not announced"

            text = (
                f"🎬 {movie_title}\n\n"
                f"🎭 Theatrical: {theatrical_str}\n"
                f"⏳ {countdown}\n"
                f"💻 Digital: {digital}\n"
                f"💿 Physical: {physical}"
            )
            await update.message.reply_text(text)
        except Exception:
            logger.exception("Error fetching release events for movie_id=%s (%s)", movie_id, movie_title)
            await update.message.reply_text(f"⚠️ Could not load data for {movie_title}.")


async def cmd_upcomingshows(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    shows = get_tracked_tv(user_id)
    if not shows:
        await update.message.reply_text("You are not tracking any TV shows.")
        return

    today = date.today()
    await update.message.reply_text(f"📺 Upcoming TV Episodes ({len(shows)} tracked)")

    for tv_id, tv_title in shows:
        try:
            details = get_tv_details(tv_id)
            status = details.get("status", "Unknown")
            next_ep = details.get("next_episode_to_air")

            if not next_ep:
                await update.message.reply_text(
                    f"📺 {tv_title}\n📡 Status: {status}\nNo upcoming episodes."
                )
                continue

            s = next_ep.get("season_number", "?")
            e = next_ep.get("episode_number", "?")
            air_date = next_ep.get("air_date", "")
            countdown = _days_label(air_date, today) if air_date else "Unknown"

            await update.message.reply_text(
                f"📺 {tv_title}\n\n"
                f"📡 Status: {status}\n"
                f"Next: S{s}E{e}\n"
                f"📅 {air_date or 'Unknown'}  ⏳ {countdown}"
            )
        except Exception:
            logger.exception("Error fetching TV details for tv_id=%s (%s)", tv_id, tv_title)
            await update.message.reply_text(f"⚠️ Could not load data for {tv_title}.")


async def cmd_subscribe_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subscribe_movies(update.effective_user.id)
    await update.message.reply_text("✅ Subscribed to movie notifications.")


async def cmd_unsubscribe_movies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    unsubscribe_movies(update.effective_user.id)
    await update.message.reply_text("🔕 Unsubscribed from movie notifications.")


async def cmd_subscribe_tv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    subscribe_tv(update.effective_user.id)
    await update.message.reply_text("✅ Subscribed to TV notifications.")


async def cmd_unsubscribe_tv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    unsubscribe_tv(update.effective_user.id)
    await update.message.reply_text("🔕 Unsubscribed from TV notifications.")


# --------------------------------------------------
# Callback Handler
# --------------------------------------------------

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    logger.debug("Callback from user=%s data=%s", user_id, data)

    if data.startswith("details:"):
        idx = int(data.split(":")[1])
        results = movie_cache.get(user_id)
        if results is None or idx >= len(results):
            await query.message.reply_text("Search results expired. Run /search again.")
            return
        await _send_movie_detail(query, results[idx])

    elif data.startswith("tvdetails:"):
        idx = int(data.split(":")[1])
        results = tv_cache.get(user_id)
        if results is None or idx >= len(results):
            await query.message.reply_text("Search results expired. Run /searchtv again.")
            return
        await _send_tv_detail(query, results[idx])

    elif data.startswith("track:"):
        idx = int(data.split(":")[1])
        results = movie_cache.get(user_id)
        if results is None or idx >= len(results):
            await query.message.reply_text("Search results expired. Run /search again.")
            return
        movie = results[idx]
        movie_id = movie["id"]
        movie_title = movie.get("title", "Unknown")
        track_movie(user_id, movie_id, movie_title)
        keyboard = [[
            InlineKeyboardButton("Details", callback_data=f"details:{idx}"),
            InlineKeyboardButton("Tracked ✓", callback_data="tracked"),
        ]]
        await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
        await query.message.reply_text(f"✅ Now tracking: {movie_title}")

    elif data.startswith("tvtrack:"):
        idx = int(data.split(":")[1])
        results = tv_cache.get(user_id)
        if results is None or idx >= len(results):
            await query.message.reply_text("Search results expired. Run /searchtv again.")
            return
        show = results[idx]
        tv_id = show["id"]
        tv_title = show.get("name", "Unknown")
        track_tv(user_id, tv_id, tv_title)
        keyboard = [[
            InlineKeyboardButton("Details", callback_data=f"tvdetails:{idx}"),
            InlineKeyboardButton("Tracked ✓", callback_data="tvtracked"),
        ]]
        await query.edit_message_reply_markup(InlineKeyboardMarkup(keyboard))
        await query.message.reply_text(f"✅ Now tracking: {tv_title}")

    elif data.startswith("untrack:"):
        movie_id = int(data.split(":")[1])
        untrack_movie(user_id, movie_id)
        await query.edit_message_text("❌ Movie removed from tracking.")

    elif data.startswith("untracktv:"):
        tv_id = int(data.split(":")[1])
        untrack_tv(user_id, tv_id)
        await query.edit_message_text("❌ TV show removed from tracking.")

    elif data in ("tracked", "tvtracked"):
        await query.answer("Already tracked.", show_alert=False)


# --------------------------------------------------
# Entry Point
# --------------------------------------------------

def main() -> None:
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CallbackQueryHandler(button_callback))

    commands = [
        ("start", cmd_start),
        ("ping", cmd_ping),
        ("today", cmd_today),
        ("date", cmd_date),
        ("search", cmd_search),
        ("searchtv", cmd_searchtv),
        ("mymovies", cmd_mymovies),
        ("myshows", cmd_myshows),
        ("comingsoon", cmd_comingsoon),
        ("upcomingshows", cmd_upcomingshows),
        ("subscribe_movies", cmd_subscribe_movies),
        ("unsubscribe_movies", cmd_unsubscribe_movies),
        ("subscribe_tv", cmd_subscribe_tv),
        ("unsubscribe_tv", cmd_unsubscribe_tv),
    ]
    for name, handler in commands:
        app.add_handler(CommandHandler(name, handler))

    logger.info("Bot started.")
    app.run_polling()


if __name__ == "__main__":
    main()
