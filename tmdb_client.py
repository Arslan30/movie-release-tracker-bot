import logging
from datetime import date
from urllib.parse import quote

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config import TMDB_API_KEY

logger = logging.getLogger(__name__)

TMDB_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"

# Shared session with automatic retries on transient failures
_session = requests.Session()
_adapter = HTTPAdapter(
    max_retries=Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
)
_session.mount("https://", _adapter)


def _get(path: str, **params) -> dict:
    """Make an authenticated GET request to the TMDB API."""
    params["api_key"] = TMDB_API_KEY
    response = _session.get(f"{TMDB_BASE}{path}", params=params, timeout=10)
    response.raise_for_status()
    return response.json()


# --------------------------------------------------
# Search
# --------------------------------------------------

def search_movies(query: str) -> list[dict]:
    data = _get("/search/movie", query=query)
    return data.get("results", [])


def search_tv(query: str) -> list[dict]:
    data = _get("/search/tv", query=query)
    return data.get("results", [])


# --------------------------------------------------
# Movie Details
# --------------------------------------------------

def get_movie_details(movie_id: int) -> dict:
    return _get(f"/movie/{movie_id}")


def get_movie_release_dates(movie_id: int) -> dict:
    return _get(f"/movie/{movie_id}/release_dates")


def get_movies_by_date(release_date: str) -> list[dict]:
    data = _get(
        "/discover/movie",
        **{
            "primary_release_date.gte": release_date,
            "primary_release_date.lte": release_date,
        },
    )
    return data.get("results", [])


def get_movies_today() -> list[dict]:
    today = date.today().isoformat()
    return get_movies_by_date(today)


def get_release_events(movie_id: int) -> dict[str, str]:
    """Return a dict of {event_type: date_str} for US releases."""
    data = get_movie_release_dates(movie_id)
    events: dict[str, str] = {}

    for country in data.get("results", []):
        if country.get("iso_3166_1") != "US":
            continue
        for release in country.get("release_dates", []):
            release_type = release.get("type")
            release_date = release.get("release_date", "")[:10]
            if not release_date:
                continue
            if release_type == 3:
                events["theatrical"] = release_date
            elif release_type == 4:
                events["digital"] = release_date
            elif release_type == 5:
                events["physical"] = release_date

    return events


# --------------------------------------------------
# TV Details
# --------------------------------------------------

def get_tv_details(tv_id: int) -> dict:
    return _get(f"/tv/{tv_id}")


def get_tv_by_date(release_date: str) -> list[dict]:
    data = _get(
        "/discover/tv",
        **{
            "first_air_date.gte": release_date,
            "first_air_date.lte": release_date,
        },
    )
    return data.get("results", [])


def get_next_episode_info(tv_id: int) -> dict | None:
    details = get_tv_details(tv_id)
    next_ep = details.get("next_episode_to_air")
    if not next_ep:
        return None
    return {
        "name": next_ep.get("name", "Unknown"),
        "season": next_ep.get("season_number"),
        "episode": next_ep.get("episode_number"),
        "air_date": next_ep.get("air_date"),
    }


# --------------------------------------------------
# Utilities
# --------------------------------------------------

def get_poster_url(poster_path: str | None) -> str | None:
    if not poster_path:
        return None
    return f"{POSTER_BASE}{poster_path}"
