from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
)
from database import (
    init_db,
    subscribe_movies,
    unsubscribe_movies,
    subscribe_tv,
    is_movie_tracked,
    unsubscribe_tv,
    track_movie,
    untrack_movie,
    get_tracked_movies,
    track_tv,
    untrack_tv,
    get_tracked_tv,
    is_tv_tracked,
)
from datetime import date

from config import BOT_TOKEN
from tmdb_client import (
    get_movies_today,
    get_release_events,
    get_movies_by_date,
    get_next_episode_info,
    search_movies,
    search_tv,
    get_tv_details,
    get_movie_details,
    get_poster_url,
)

user_search_results = {}
user_tv_search_results = {}

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong!")

async def date_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/date YYYY-MM-DD"
        )
        return

    release_date = context.args[0]

    movies = get_movies_by_date(release_date)

    if not movies:
        await update.message.reply_text(
            f"No releases found for {release_date}"
        )
        return

    message = f"Releases on {release_date}\n\n"

    for movie in movies[:20]:

        title = movie.get("title", "Unknown")
        rating = movie.get("vote_average", "N/A")

        release_date_movie = movie.get("release_date", "")

        year = release_date_movie[:4] if release_date_movie else "?"

        message += f"• {title} ({year}) ⭐ {rating}\n"

    await update.message.reply_text(message)\

async def comingsoon(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    movies = get_tracked_movies(
        user_id
    )

    if not movies:

        await update.message.reply_text(
            "You are not tracking any movies."
        )

        return

    today = date.today()

    message = "🎬 Upcoming Releases\n\n"

    for (
        movie_id,
        movie_title
    ) in movies:

        try:

            events = get_release_events(
                movie_id
            )

            theatrical = events.get(
                "theatrical"
            )

            digital = events.get(
                "digital",
                "Not announced"
            )

            physical = events.get(
                "physical",
                "Not announced"
            )

            if theatrical:

                release_date = date.fromisoformat(
                    theatrical
                )

                days_left = (
                    release_date - today
                ).days

                countdown = (
                    f"{days_left} days"
                    if days_left >= 0
                    else "Released"
                )

            else:

                theatrical = (
                    "Not announced"
                )

                countdown = "Unknown"

            message += (
                f"🎬 {movie_title}\n\n"
                f"🎭 Theatrical: "
                f"{theatrical}\n"
                f"⏳ {countdown}\n"
                f"💻 Digital: "
                f"{digital}\n"
                f"💿 Physical: "
                f"{physical}\n\n"
            )

        except Exception:

            continue

    await update.message.reply_text(
        message[:4000]
    )

async def movie_button_details(
    query,
    movie
):

    movie_id = movie["id"]

    details = get_movie_details(
        movie_id
    )

    events = get_release_events(
        movie_id
    )

    poster_path = details.get(
        "poster_path"
    )

    poster_url = get_poster_url(
        poster_path
    )

    title = details.get(
        "title",
        "Unknown"
    )

    rating = details.get(
        "vote_average",
        "N/A"
    )

    vote_count = details.get(
        "vote_count",
        0
    )

    overview = details.get(
        "overview",
        "No overview available."
    )

    runtime = details.get(
        "runtime",
        "?"
    )

    status = details.get(
        "status",
        "Unknown"
    )

    release_date = details.get(
        "release_date",
        ""
    )

    year = (
        release_date[:4]
        if release_date
        else "?"
    )

    genres = ", ".join(
        genre["name"]
        for genre in details.get(
            "genres",
            []
        )
    )

    if not genres:
        genres = "Unknown"

    theatrical = events.get(
        "theatrical",
        "Not announced"
    )

    digital = events.get(
        "digital",
        "Not announced"
    )

    physical = events.get(
        "physical",
        "Not announced"
    )

    message = (
        f"🎬 {title} ({year})\n\n"
        f"⭐ Rating: {rating} "
        f"({vote_count:,} votes)\n"
        f"⏱ Runtime: {runtime} min\n"
        f"📡 Status: {status}\n"
        f"🏷 Genres: {genres}\n\n"
        f"🎭 Theatrical: {theatrical}\n"
        f"💻 Digital: {digital}\n"
        f"💿 Physical/Blu-ray: {physical}\n\n"
        f"{overview[:700]}"
    )

    if poster_url:

        await query.message.reply_photo(
            photo=poster_url,
            caption=message
        )

    else:

        await query.message.reply_text(
            message
        )

async def upcomingshows(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    shows = get_tracked_tv(
        user_id
    )

    if not shows:

        await update.message.reply_text(
            "You are not tracking any TV shows."
        )

        return

    today = date.today()

    message = "📺 Upcoming TV Episodes\n\n"

    for (
        tv_id,
        tv_title
    ) in shows:

        try:

            details = get_tv_details(
                tv_id
            )

            status = details.get(
                "status",
                "Unknown"
            )

            next_episode = details.get(
                "next_episode_to_air"
            )

            if not next_episode:

                message += (
                    f"📺 {tv_title}\n\n"
                    f"📡 Status: {status}\n"
                    f"No upcoming episodes.\n\n"
                )

                continue

            season = next_episode.get(
                "season_number",
                "?"
            )

            episode = next_episode.get(
                "episode_number",
                "?"
            )

            air_date = next_episode.get(
                "air_date"
            )

            if air_date:

                episode_date = (
                    date.fromisoformat(
                        air_date
                    )
                )

                days_left = (
                    episode_date - today
                ).days

                countdown = (
                    f"{days_left} days"
                    if days_left >= 0
                    else "Released"
                )

            else:

                countdown = "Unknown"

            message += (
                f"📺 {tv_title}\n\n"
                f"📡 Status: {status}\n\n"
                f"📺 Next Episode:\n"
                f"S{season}E{episode}\n"
                f"📅 {air_date}\n"
                f"⏳ {countdown}\n\n"
            )

        except Exception:

            continue

    await update.message.reply_text(
        message[:4000]
    )

async def tv_button_details(
    query,
    show
):

    tv_id = show["id"]

    details = get_tv_details(
        tv_id
    )

    name = details.get(
        "name",
        "Unknown"
    )

    rating = details.get(
        "vote_average",
        "N/A"
    )

    vote_count = details.get(
        "vote_count",
        0
    )

    overview = details.get(
        "overview",
        "No overview available."
    )

    status = details.get(
        "status",
        "Unknown"
    )

    first_air_date = details.get(
        "first_air_date",
        ""
    )

    last_air_date = details.get(
        "last_air_date",
        ""
    )

    number_of_seasons = details.get(
        "number_of_seasons",
        "?"
    )

    number_of_episodes = details.get(
        "number_of_episodes",
        "?"
    )

    genres = ", ".join(
        genre["name"]
        for genre in details.get(
            "genres",
            []
        )
    )

    if not genres:
        genres = "Unknown"

    poster_path = details.get(
        "poster_path"
    )

    poster_url = get_poster_url(
        poster_path
    )

    next_episode = details.get(
        "next_episode_to_air"
    )

    if next_episode:

        season = next_episode.get(
            "season_number",
            "?"
        )

        episode = next_episode.get(
            "episode_number",
            "?"
        )

        air_date = next_episode.get(
            "air_date",
            "Unknown"
        )

        next_episode_text = (
            f"📺 Next Episode:\n"
            f"S{season}E{episode}\n"
            f"📅 {air_date}\n\n"
        )

    else:

        next_episode_text = (
            "📺 Next Episode:\n"
            "No upcoming episode\n\n"
        )

    year = (
        first_air_date[:4]
        if first_air_date
        else "?"
    )

    message = (
        f"📺 {name} ({year})\n\n"
        f"⭐ Rating: {rating} "
        f"({vote_count:,} votes)\n"
        f"📡 Status: {status}\n"
        f"🎞 Seasons: {number_of_seasons}\n"
        f"🎬 Episodes: {number_of_episodes}\n"
        f"🏷 Genres: {genres}\n\n"
        f"📅 First Air Date: {first_air_date}\n"
        f"📅 Last Air Date: {last_air_date}\n\n"
        f"{next_episode_text}"
        f"{overview[:700]}"
    )

    if poster_url:

        await query.message.reply_photo(
            photo=poster_url,
            caption=message
        )

    else:

        await query.message.reply_text(
            message
        )

async def button_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    data = query.data

    print(
        "CALLBACK DATA:",
        data
    )

    user_id = update.effective_user.id

    # Movie details

    if data.startswith("details:"):

        movie_index = int(
            data.split(":")[1]
        )

        if user_id not in user_search_results:
            return

        results = user_search_results[user_id]

        if movie_index >= len(results):
            return

        movie = results[movie_index]

        await movie_button_details(
            query,
            movie
        )

    # TV details

    elif data.startswith("tvdetails:"):

        show_index = int(
            data.split(":")[1]
        )

        if user_id not in user_tv_search_results:
            return

        results = user_tv_search_results[
            user_id
        ]

        if show_index >= len(results):
            return

        show = results[show_index]

        await tv_button_details(
            query,
            show
        )

    # Movie already tracked

    elif data == "tracked":

        await query.answer(
            "Already tracked."
        )

    # TV already tracked

    elif data == "tvtracked":

        await query.answer(
            "Already tracked."
        )

    # Track movie

    elif data.startswith("track:"):

        movie_index = int(
            data.split(":")[1]
        )

        if user_id not in user_search_results:
            return

        results = user_search_results[user_id]

        if movie_index >= len(results):
            return

        movie = results[movie_index]

        movie_id = movie["id"]

        movie_title = movie.get(
            "title",
            "Unknown"
        )

        track_movie(
            user_id,
            movie_id,
            movie_title
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Details",
                    callback_data=f"details:{movie_index}"
                ),
                InlineKeyboardButton(
                    "Tracked ✓",
                    callback_data="tracked"
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        await query.edit_message_reply_markup(
            reply_markup=reply_markup
        )

        await query.message.reply_text(
            f"Tracking: {movie_title}"
        )

    # Track TV

    elif data.startswith("tvtrack:"):

        show_index = int(
            data.split(":")[1]
        )

        if user_id not in user_tv_search_results:
            return

        results = user_tv_search_results[
            user_id
        ]

        if show_index >= len(results):
            return

        show = results[show_index]

        tv_id = show["id"]

        tv_title = show.get(
            "name",
            "Unknown"
        )

        track_tv(
            user_id,
            tv_id,
            tv_title
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Details",
                    callback_data=f"tvdetails:{show_index}"
                ),
                InlineKeyboardButton(
                    "Tracked ✓",
                    callback_data="tvtracked"
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        await query.edit_message_reply_markup(
            reply_markup=reply_markup
        )

        await query.message.reply_text(
            f"Tracking: {tv_title}"
        )

    # Untrack movie

    elif data.startswith("untrack:"):

        movie_id = int(
            data.split(":")[1]
        )

        untrack_movie(
            user_id,
            movie_id
        )

        await query.edit_message_text(
            "Movie removed from tracking."
        )

    # Untrack TV

    elif data.startswith("untracktv:"):

        tv_id = int(
            data.split(":")[1]
        )

        untrack_tv(
            user_id,
            tv_id
        )

        await query.edit_message_text(
            "TV show removed from tracking."
        )


async def subscribe_movies_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    subscribe_movies(user_id)

    await update.message.reply_text(
        "Subscribed to movie notifications."
    )

async def unsubscribe_movies_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    unsubscribe_movies(user_id)

    await update.message.reply_text(
        "Unsubscribed from movie notifications."
    )

async def subscribe_tv_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    subscribe_tv(user_id)

    await update.message.reply_text(
        "Subscribed to TV notifications."
    )

async def unsubscribe_tv_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    unsubscribe_tv(user_id)

    await update.message.reply_text(
        "Unsubscribed from TV notifications."
    )


async def mymovies(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    movies = get_tracked_movies(user_id)

    if not movies:

        await update.message.reply_text(
            "You are not tracking any movies."
        )

        return

    for movie_id, movie_title in movies:

        keyboard = [
            [
                InlineKeyboardButton(
                    "Untrack",
                    callback_data=f"untrack:{movie_id}"
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        await update.message.reply_text(
            movie_title,
            reply_markup=reply_markup
        )

async def searchtv(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "Usage:\n/searchtv show name"
        )

        return

    query = " ".join(
        context.args
    )

    results = search_tv(
        query
    )

    if not results:

        await update.message.reply_text(
            f"No results found for '{query}'"
        )

        return

    user_id = update.effective_user.id

    results = results[:10]

    user_tv_search_results[user_id] = (
        results
    )

    for i, show in enumerate(results):

        name = show.get(
            "name",
            "Unknown"
        )

        rating = show.get(
            "vote_average",
            "N/A"
        )

        first_air_date = show.get(
            "first_air_date",
            ""
        )

        year = (
            first_air_date[:4]
            if first_air_date
            else "?"
        )

        tv_id = show["id"]

        if is_tv_tracked(
            user_id,
            tv_id
        ):

            track_button = (
                InlineKeyboardButton(
                    "Tracked ✓",
                    callback_data="tvtracked"
                )
            )

        else:

            track_button = (
                InlineKeyboardButton(
                    "Track",
                    callback_data=f"tvtrack:{i}"
                )
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Details",
                    callback_data=f"tvdetails:{i}"
                ),
                track_button
            ]
        ]

        reply_markup = (
            InlineKeyboardMarkup(
                keyboard
            )
        )

        await update.message.reply_text(
            (
                f"📺 {name} ({year})\n"
                f"⭐ {rating}"
            ),
            reply_markup=reply_markup
        )

async def myshows(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    shows = get_tracked_tv(
        user_id
    )

    if not shows:

        await update.message.reply_text(
            "You are not tracking any TV shows."
        )

        return

    for tv_id, tv_title in shows:

        keyboard = [
            [
                InlineKeyboardButton(
                    "Untrack",
                    callback_data=f"untracktv:{tv_id}"
                )
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        await update.message.reply_text(
            tv_title,
            reply_markup=reply_markup
        )

async def search(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not context.args:

        await update.message.reply_text(
            "Usage:\n/search movie name"
        )

        return

    query = " ".join(
        context.args
    )

    results = search_movies(
        query
    )

    if not results:

        await update.message.reply_text(
            f"No results found for '{query}'"
        )

        return

    user_id = update.effective_user.id

    results = results[:10]

    user_search_results[user_id] = results

    for i, movie in enumerate(results):

        title = movie.get(
            "title",
            "Unknown"
        )

        rating = movie.get(
            "vote_average",
            "N/A"
        )

        release_date = movie.get(
            "release_date",
            ""
        )

        year = (
            release_date[:4]
            if release_date
            else "?"
        )

        movie_id = movie["id"]

        if is_movie_tracked(
            user_id,
            movie_id
        ):

            track_button = (
                InlineKeyboardButton(
                    "Tracked ✓",
                    callback_data="tracked"
                )
            )

        else:

            track_button = (
                InlineKeyboardButton(
                    "Track",
                    callback_data=f"track:{i}"
                )
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "Details",
                    callback_data=f"details:{i}"
                ),
                track_button,
            ]
        ]

        reply_markup = InlineKeyboardMarkup(
            keyboard
        )

        await update.message.reply_text(
            (
                f"🎬 {title} ({year})\n"
                f"⭐ {rating}"
            ),
            reply_markup=reply_markup
        )


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    movies = get_movies_today()

    if not movies:
        await update.message.reply_text("No releases found.")
        return

    message = "Today's Releases\n\n"

    for movie in movies[:20]:

        title = movie.get("title", "Unknown")
        rating = movie.get("vote_average", "N/A")

        release_date = movie.get("release_date", "")

        year = release_date[:4] if release_date else "?"

        message += f"• {title} ({year}) ⭐ {rating}\n"

    await update.message.reply_text(message)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
    "Movie Release Tracker\n\n"
    "/today - Today's releases\n"
    "/date YYYY-MM-DD\n"
    "/search movie name\n"
    "/searchtv show name\n"
    "/upcomingshows\n"
    "/mymovies\n"
    "/myshows\n"
    "/comingsoon\n"
    "/subscribe_movies\n"
    "/unsubscribe_movies\n"
    "/subscribe_tv\n"
    "/unsubscribe_tv\n"
    "/ping"
)

def main():

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()


    app.add_handler(
    CallbackQueryHandler(
        button_callback
        )
    )

    app.add_handler(
        CommandHandler(
            "subscribe_movies",
            subscribe_movies_command
        )
    )

    app.add_handler(
    CommandHandler(
        "upcomingshows",
        upcomingshows
        )
    )

    app.add_handler(
        CommandHandler(
            "unsubscribe_movies",
            unsubscribe_movies_command
        )
    )

    app.add_handler(
    CommandHandler(
        "myshows",
        myshows
        )
    )

    app.add_handler(
    CommandHandler(
        "mymovies",
        mymovies
       )
    )

    app.add_handler(
        CommandHandler(
            "subscribe_tv",
            subscribe_tv_command
        )
    )

    app.add_handler(
    CommandHandler(
        "comingsoon",
        comingsoon
       )
    )

    app.add_handler(
        CommandHandler(
            "unsubscribe_tv",
            unsubscribe_tv_command
        )
    )

    app.add_handler(CommandHandler("searchtv", searchtv))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("date", date_command))
    app.add_handler(CommandHandler("today", today))

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))

    print("Bot started...")

    app.run_polling()


if __name__ == "__main__":
    main()