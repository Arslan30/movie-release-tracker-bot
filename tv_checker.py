import requests

from datetime import date

from config import BOT_TOKEN

from database import (
    get_all_tracked_tv,
    notification_sent_tv,
    mark_notification_sent_tv,
)

from tmdb_client import (
    get_tv_details,
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
            "text": text
        },
        timeout=20
    )

    response.raise_for_status()


def check_tv_shows():

    shows = get_all_tracked_tv()

    print(
        f"Checking {len(shows)} shows..."
    )

    for (
        user_id,
        tv_id,
        tv_title
    ) in shows:

        try:

            details = get_tv_details(
                tv_id
            )

            next_episode = details.get(
                "next_episode_to_air"
            )

            if not next_episode:

                print(
                    f"{tv_title} -> "
                    f"No upcoming episode"
                )

                continue

            air_date = next_episode.get(
                "air_date"
            )

            season = next_episode.get(
                "season_number"
            )

            episode = next_episode.get(
                "episode_number"
            )

            print(
                f"{tv_title} -> "
                f"S{season}E{episode} "
                f"({air_date})"
            )

            if (
                air_date == today
                and not notification_sent_tv(
                    user_id,
                    tv_id,
                    season,
                    episode
                )
            ):

                send_message(
                    user_id,
                    (
                        f"📺 {tv_title}\n\n"
                        f"New episode released today!\n\n"
                        f"Season {season}\n"
                        f"Episode {episode}\n"
                        f"📅 {air_date}"
                    )
                )

                mark_notification_sent_tv(
                    user_id,
                    tv_id,
                    season,
                    episode
                )

                print(
                    f"Notification sent: "
                    f"{tv_title}"
                )

        except Exception as e:

            print(
                f"Error checking "
                f"{tv_title}: {e}"
            )


if __name__ == "__main__":

    print(
        f"TV Checker Started "
        f"({today})"
    )

    check_tv_shows()

    print("Done.")