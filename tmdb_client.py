import requests
from datetime import date

from config import TMDB_API_KEY


def get_movies_by_date(release_date):
    url = (
        "https://api.themoviedb.org/3/discover/movie"
        f"?api_key={TMDB_API_KEY}"
        f"&primary_release_date.gte={release_date}"
        f"&primary_release_date.lte={release_date}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json().get("results", [])

def get_next_episode_info(
    tv_id
):

    details = get_tv_details(
        tv_id
    )

    next_episode = details.get(
        "next_episode_to_air"
    )

    if not next_episode:
        return None

    return {
        "name": next_episode.get(
            "name",
            "Unknown"
        ),
        "season": next_episode.get(
            "season_number"
        ),
        "episode": next_episode.get(
            "episode_number"
        ),
        "air_date": next_episode.get(
            "air_date"
        )
    }

def get_poster_url(
    poster_path
):

    if not poster_path:
        return None

    return (
        "https://image.tmdb.org/t/p/w500"
        f"{poster_path}"
    )

def search_movies(query):
    url = (
        "https://api.themoviedb.org/3/search/movie"
        f"?api_key={TMDB_API_KEY}"
        f"&query={query}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json().get("results", [])

def search_tv(query):
    url = (
        "https://api.themoviedb.org/3/search/tv"
        f"?api_key={TMDB_API_KEY}"
        f"&query={query}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json().get("results", [])
def get_movie_details(movie_id):

    url = (
        f"https://api.themoviedb.org/3/movie/{movie_id}"
        f"?api_key={TMDB_API_KEY}"
    )

    response = requests.get(
        url,
        timeout=10
    )

    response.raise_for_status()

    return response.json()
def get_tv_details(tv_id):
    url = (
        f"https://api.themoviedb.org/3/tv/{tv_id}"
        f"?api_key={TMDB_API_KEY}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json()

def get_movies_today():
    today = date.today().strftime("%Y-%m-%d")

    url = (
        "https://api.themoviedb.org/3/discover/movie"
        f"?api_key={TMDB_API_KEY}"
        f"&primary_release_date.gte={today}"
        f"&primary_release_date.lte={today}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json().get("results", [])

def get_movie_release_dates(
    movie_id
):

    url = (
        f"https://api.themoviedb.org/3/movie/"
        f"{movie_id}/release_dates"
        f"?api_key={TMDB_API_KEY}"
    )

    response = requests.get(
        url,
        timeout=10
    )

    response.raise_for_status()

    return response.json()

def get_release_events(movie_id):

    data = get_movie_release_dates(
        movie_id
    )

    events = {}

    for country in data["results"]:

        if country["iso_3166_1"] != "US":
            continue

        for release in country[
            "release_dates"
        ]:

            release_type = release["type"]

            release_date = (
                release["release_date"][:10]
            )

            if release_type == 3:
                events["theatrical"] = release_date

            elif release_type == 4:
                events["digital"] = release_date

            elif release_type == 5:
                events["physical"] = release_date

    return events

def get_tv_by_date(release_date):
    url = (
        "https://api.themoviedb.org/3/discover/tv"
        f"?api_key={TMDB_API_KEY}"
        f"&first_air_date.gte={release_date}"
        f"&first_air_date.lte={release_date}"
    )

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.json().get("results", [])