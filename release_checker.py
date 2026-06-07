import requests

from datetime import date

from config import BOT_TOKEN

from database import (
    get_all_tracked_movies,
    notification_sent,
    mark_notification_sent,
)

from tmdb_client import (
    get_release_events,
)

today = date.today().strftime(
    "%Y-%m-%d"
)


def send_message(
    user_id,
    text
):

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": user_id,
            "text": text,
        },
        timeout=20,
    )

    response.raise_for_status()


def check_movies():

    movies = get_all_tracked_movies()

    print(
        f"Checking {len(movies)} tracked movies..."
    )

    for (
        user_id,
        movie_id,
        movie_title,
    ) in movies:

        try:

            events = get_release_events(
                movie_id
            )

            print(
                f"{movie_title} -> "
                f"{events}"
            )

            for (
                event_type,
                event_date,
            ) in events.items():

                if (
                    event_date == today
                    and not notification_sent(
                        user_id,
                        movie_id,
                        event_type,
                    )
                ):

                    if (
                        event_type
                        == "theatrical"
                    ):

                        message = (
                            f"🎬 {movie_title}\n\n"
                            f"🎭 Theatrical release today!\n"
                            f"📅 {event_date}"
                        )

                    elif (
                        event_type
                        == "digital"
                    ):

                        message = (
                            f"🎬 {movie_title}\n\n"
                            f"💻 Digital release today!\n"
                            f"📅 {event_date}"
                        )

                    elif (
                        event_type
                        == "physical"
                    ):

                        message = (
                            f"🎬 {movie_title}\n\n"
                            f"💿 Physical/Blu-ray "
                            f"release today!\n"
                            f"📅 {event_date}"
                        )

                    else:

                        message = (
                            f"🎬 {movie_title}\n\n"
                            f"{event_type} "
                            f"release today!\n"
                            f"📅 {event_date}"
                        )

                    send_message(
                        user_id,
                        message
                    )

                    mark_notification_sent(
                        user_id,
                        movie_id,
                        event_type,
                    )

                    print(
                        f"Notification sent: "
                        f"{movie_title} "
                        f"({event_type})"
                    )

        except Exception as e:

            print(
                f"Error checking "
                f"{movie_title}: {e}"
            )


if __name__ == "__main__":

    print(
        f"Release Checker Started "
        f"({today})"
    )

    check_movies()

    print("Done.")