from __future__ import annotations

import json
import os
import re
from typing import Any, Iterable

import requests

# Support both package and standalone imports
try:
    from .database import (
        get_db_context,
        metadata_cache_get,
        metadata_cache_get_no_ttl,
        metadata_cache_set,
        rating_cache_get,
        rating_cache_get_no_ttl,
        rating_cache_set,
    )
    from .models import SearchResult
except ImportError:
    from database import (
        get_db_context,
        metadata_cache_get,
        metadata_cache_get_no_ttl,
        metadata_cache_set,
        rating_cache_get,
        rating_cache_get_no_ttl,
        rating_cache_set,
    )
    from models import SearchResult

IMDB_SUGGESTION_URL = "https://v3.sg.media-imdb.com/suggestion/{first}/{query}.json"
IMDB_TITLE_URL = "https://www.imdb.com/title/{title_id}/"
IMDB_TRENDING_URL = "https://www.imdb.com/chart/moviemeter/"
OMDB_URL = "https://www.omdbapi.com/"
TMDB_TRENDING_URL = "https://api.themoviedb.org/3/trending/all/week"
TMDB_EXTERNAL_IDS_URL = "https://api.themoviedb.org/3/{media_type}/{tmdb_id}/external_ids"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w185"
DEFAULT_USER_AGENT = "shovo-movielist/1.0 (+https://example.com)"
MAX_RESULTS = 10
ALLOWED_TYPE_LABELS = {"feature", "movie", "tvseries", "tvminiseries", "tvmovie"}
OMDB_API_KEY = os.environ.get("OMDB_API_KEY", "thewdb")
TMDB_ACCESS_TOKEN = os.environ.get("TMDB_ACCESS_TOKEN")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
DEFAULT_TRENDING_TITLE_IDS = tuple(
    title_id.strip()
    for title_id in os.environ.get(
        "SHOVO_TRENDING_FALLBACK_IDS",
        "tt0111161,tt0068646,tt0468569,tt0109830,tt0137523,tt1375666,tt0816692,tt0133093,tt0120737,tt0167260",
    ).split(",")
    if title_id.strip()
)


def normalize_type_label(type_label: str | None) -> str:
    """Normalize a type label to lowercase alphanumeric."""
    if not type_label:
        return ""
    return re.sub(r"[^a-z]", "", type_label.lower())


def shrink_image_url(url: str | None) -> str | None:
    """Resize IMDB image URL to a smaller size."""
    if not url:
        return None
    match = re.search(r"\._V1_.*(\.jpg|\.png)$", url)
    if not match:
        return url
    return re.sub(
        r"\._V1_.*(\.jpg|\.png)$",
        r"._V1_UX120_CR0,0,120,180_AL_\1",
        url,
    )


def _parse_omdb_ratings(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Parse IMDB and Rotten Tomatoes ratings from an OMDB payload."""
    imdb_rating = payload.get("imdbRating")
    if not imdb_rating or imdb_rating == "N/A":
        imdb_rating = None
    rotten_rating = None
    ratings = payload.get("Ratings") or []
    for rating in ratings:
        if rating.get("Source") == "Rotten Tomatoes":
            rotten_rating = rating.get("Value")
            break
    return imdb_rating, rotten_rating


def _fetch_rotten_tomatoes(title_id: str, user_agent: str) -> str | None:
    """Fetch Rotten Tomatoes rating from OMDB API."""
    payload = _fetch_omdb_title(title_id, user_agent)
    if not payload:
        return None
    return _parse_omdb_ratings(payload)[1]


def _fetch_omdb_title(title_id: str, user_agent: str, season: int | None = None) -> dict[str, Any]:
    """Fetch title info from OMDB API."""
    if not OMDB_API_KEY:
        return {}
    params: dict[str, Any] = {"i": title_id, "apikey": OMDB_API_KEY}
    if season is not None:
        params["Season"] = season
    response = requests.get(
        OMDB_URL,
        params=params,
        headers={"User-Agent": user_agent},
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("Response") != "True":
        return {}
    return payload


def _parse_runtime(runtime: str | None) -> int | None:
    """Parse runtime string to minutes."""
    if not runtime or runtime == "N/A":
        return None
    match = re.search(r"(\d+)", runtime)
    if not match:
        return None
    return int(match.group(1))


def _parse_original_language(value: str | None) -> str | None:
    """Parse original language from comma-separated list."""
    if not value or value == "N/A":
        return None
    language = value.split(",")[0].strip()
    return language or None


def _fetch_metadata(
    title_id: str, user_agent: str, normalized_type: str
) -> tuple[int | None, int | None, int | None, int | None, str | None]:
    """Fetch metadata from OMDB API."""
    payload = _fetch_omdb_title(title_id, user_agent)
    runtime_minutes = _parse_runtime(payload.get("Runtime"))
    original_language = _parse_original_language(payload.get("Language"))
    total_seasons = payload.get("totalSeasons")
    try:
        total_seasons_int = int(total_seasons) if total_seasons else None
    except ValueError:
        total_seasons_int = None
    avg_episode_length = runtime_minutes if normalized_type in {"tvseries", "tvminiseries"} else None
    total_episodes = None
    if normalized_type == "tvminiseries" and total_seasons_int:
        total_episodes_count = 0
        for season in range(1, total_seasons_int + 1):
            season_payload = _fetch_omdb_title(title_id, user_agent, season=season)
            episodes = season_payload.get("Episodes") or []
            total_episodes_count += len(episodes)
        total_episodes = total_episodes_count if total_episodes_count else None
    return runtime_minutes, total_seasons_int, total_episodes, avg_episode_length, original_language


def get_metadata(
    title_id: str, user_agent: str, normalized_type: str
) -> tuple[int | None, int | None, int | None, int | None, str | None]:
    """Get metadata for a title, using cache if available (no TTL — metadata rarely changes)."""
    with get_db_context() as conn:
        cached = metadata_cache_get_no_ttl(conn, title_id)
        if cached is not None:
            return cached
        try:
            metadata = _fetch_metadata(title_id, user_agent, normalized_type)
        except requests.RequestException:
            metadata = (None, None, None, None, None)
        metadata_cache_set(conn, title_id, *metadata)
        conn.commit()
        return metadata


def _fetch_ratings(title_id: str, user_agent: str) -> tuple[str | None, str | None]:
    """Fetch IMDB and Rotten Tomatoes ratings, preferring OMDB over brittle IMDB scraping."""
    try:
        payload = _fetch_omdb_title(title_id, user_agent)
        if payload:
            imdb_rating, rotten_rating = _parse_omdb_ratings(payload)
            if imdb_rating or rotten_rating:
                return imdb_rating, rotten_rating
    except requests.RequestException:
        pass

    headers = {"User-Agent": user_agent}
    response = requests.get(IMDB_TITLE_URL.format(title_id=title_id), headers=headers, timeout=10)
    response.raise_for_status()
    match = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.text, re.S)
    if not match:
        return None, None
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        data = {}
    imdb_rating = data.get("aggregateRating", {}).get("ratingValue")
    return str(imdb_rating) if imdb_rating is not None else None, None


def get_ratings(title_id: str, user_agent: str) -> tuple[str | None, str | None]:
    """Get ratings for a title, using cache if available."""
    with get_db_context() as conn:
        cached = rating_cache_get(conn, title_id)
        if cached is not None:
            return cached
        try:
            imdb_rating, rotten_rating = _fetch_ratings(title_id, user_agent)
        except requests.RequestException:
            imdb_rating, rotten_rating = None, None
        rating_cache_set(conn, title_id, imdb_rating, rotten_rating)
        conn.commit()
        return imdb_rating, rotten_rating



def parse_suggestion_item(
    item: dict[str, Any], user_agent: str, include_details: bool = True
) -> SearchResult | None:
    """Parse an IMDB suggestion item into a SearchResult."""
    title_id = item.get("id")
    if not title_id:
        return None
    type_label = item.get("qid") or item.get("q")
    normalized_type = normalize_type_label(type_label)
    if normalized_type not in ALLOWED_TYPE_LABELS:
        return None
    image_url = item.get("i", {}).get("imageUrl")
    runtime_minutes = total_seasons = total_episodes = avg_episode_length = None
    original_language = None
    rating = rotten_tomatoes = None
    if include_details:
        (
            runtime_minutes,
            total_seasons,
            total_episodes,
            avg_episode_length,
            original_language,
        ) = get_metadata(title_id, user_agent, normalized_type)
        rating, rotten_tomatoes = get_ratings(title_id, user_agent)
    else:
        # For search results: serve cached data without fetching from external APIs
        with get_db_context() as conn:
            cached_meta = metadata_cache_get_no_ttl(conn, title_id)
            if cached_meta:
                runtime_minutes, total_seasons, total_episodes, avg_episode_length, original_language = cached_meta
            cached_rating = rating_cache_get_no_ttl(conn, title_id)
            if cached_rating:
                rating, rotten_tomatoes = cached_rating
    return SearchResult(
        title_id=title_id,
        title=item.get("l") or "Untitled",
        year=str(item.get("y")) if item.get("y") else None,
        original_language=original_language,
        type_label=type_label,
        image=shrink_image_url(image_url),
        rating=rating,
        rotten_tomatoes=rotten_tomatoes,
        runtime_minutes=runtime_minutes,
        total_seasons=total_seasons,
        total_episodes=total_episodes,
        avg_episode_length=avg_episode_length,
    )


def fetch_suggestions(query: str, user_agent: str) -> list[SearchResult]:
    """Fetch search suggestions from IMDB."""
    if not query:
        return []
    safe_query = query.strip().lower()
    if not safe_query:
        return []
    first = safe_query[0]
    url = IMDB_SUGGESTION_URL.format(first=first, query=requests.utils.quote(safe_query))
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    payload = response.json()
    items: Iterable[dict[str, Any]] = payload.get("d", [])
    results: list[SearchResult] = []
    for item in items:
        parsed = parse_suggestion_item(item, user_agent, include_details=False)
        if parsed:
            results.append(parsed)
    return results


def fetch_title_by_id(title_id: str, user_agent: str) -> SearchResult | None:
    """Fetch a single title by its IMDB ID."""
    if not title_id:
        return None
    first = title_id[0].lower()
    url = IMDB_SUGGESTION_URL.format(first=first, query=requests.utils.quote(title_id))
    headers = {"User-Agent": user_agent}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    payload = response.json()
    items: Iterable[dict[str, Any]] = payload.get("d", [])
    for item in items:
        if item.get("id") == title_id:
            return parse_suggestion_item(item, user_agent, include_details=False)
    return None


def _tmdb_headers(user_agent: str) -> dict[str, str]:
    """Build headers for TMDB API requests."""
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    if TMDB_ACCESS_TOKEN:
        headers["Authorization"] = f"Bearer {TMDB_ACCESS_TOKEN}"
    return headers


def _tmdb_params() -> dict[str, str]:
    """Build query parameters for TMDB API requests."""
    return {"api_key": TMDB_API_KEY} if TMDB_API_KEY and not TMDB_ACCESS_TOKEN else {}


def _tmdb_is_configured() -> bool:
    """Return whether TMDB credentials are available."""
    return bool(TMDB_ACCESS_TOKEN or TMDB_API_KEY)


def _fetch_tmdb_imdb_id(tmdb_id: int, media_type: str, user_agent: str) -> str | None:
    """Fetch the IMDB ID for a TMDB movie or TV result."""
    if media_type not in {"movie", "tv"}:
        return None
    response = requests.get(
        TMDB_EXTERNAL_IDS_URL.format(media_type=media_type, tmdb_id=tmdb_id),
        headers=_tmdb_headers(user_agent),
        params=_tmdb_params(),
        timeout=10,
    )
    response.raise_for_status()
    imdb_id = response.json().get("imdb_id")
    return imdb_id if isinstance(imdb_id, str) and imdb_id.startswith("tt") else None


def _parse_tmdb_year(item: dict[str, Any]) -> str | None:
    """Extract a year from a TMDB movie or TV result."""
    date_value = item.get("release_date") or item.get("first_air_date")
    if isinstance(date_value, str) and len(date_value) >= 4:
        return date_value[:4]
    return None


def _parse_tmdb_image(item: dict[str, Any]) -> str | None:
    """Build a TMDB poster URL."""
    poster_path = item.get("poster_path")
    return f"{TMDB_IMAGE_BASE_URL}{poster_path}" if poster_path else None


def _parse_tmdb_rating(item: dict[str, Any]) -> str | None:
    """Parse TMDB vote average for display."""
    rating = item.get("vote_average")
    if not isinstance(rating, (int, float)) or rating <= 0:
        return None
    return f"{rating:.1f}"


def _parse_tmdb_item(item: dict[str, Any], user_agent: str) -> SearchResult | None:
    """Parse a TMDB trending item into a SearchResult."""
    media_type = item.get("media_type")
    if media_type not in {"movie", "tv"}:
        return None
    tmdb_id = item.get("id")
    if not isinstance(tmdb_id, int):
        return None
    imdb_id = _fetch_tmdb_imdb_id(tmdb_id, media_type, user_agent)
    if not imdb_id:
        return None
    title = item.get("title") or item.get("name") or "Untitled"
    type_label = "movie" if media_type == "movie" else "tvseries"
    return SearchResult(
        title_id=imdb_id,
        title=title,
        year=_parse_tmdb_year(item),
        original_language=item.get("original_language"),
        type_label=type_label,
        image=_parse_tmdb_image(item),
        rating=_parse_tmdb_rating(item),
        rotten_tomatoes=None,
        runtime_minutes=None,
        total_seasons=None,
        total_episodes=None,
        avg_episode_length=None,
    )


def fetch_tmdb_trending(user_agent: str) -> list[SearchResult]:
    """Fetch real trending titles from TMDB."""
    if not _tmdb_is_configured():
        return []
    response = requests.get(
        TMDB_TRENDING_URL,
        headers=_tmdb_headers(user_agent),
        params={**_tmdb_params(), "language": "en-US"},
        timeout=10,
    )
    response.raise_for_status()
    results: list[SearchResult] = []
    for item in response.json().get("results", []):
        if item.get("adult"):
            continue
        parsed = _parse_tmdb_item(item, user_agent)
        if parsed:
            results.append(parsed)
        if len(results) >= MAX_RESULTS:
            break
    return results


def _titles_from_ids(title_ids: Iterable[str], user_agent: str) -> list[SearchResult]:
    """Fetch title summaries for a list of IMDB IDs."""
    seen: set[str] = set()
    results: list[SearchResult] = []
    for title_id in title_ids:
        if title_id in seen:
            continue
        seen.add(title_id)
        result = fetch_title_by_id(title_id, user_agent)
        if result:
            results.append(result)
        if len(results) >= MAX_RESULTS:
            break
    return results


def fetch_trending(user_agent: str) -> list[SearchResult]:
    """Fetch real trending titles, preferring TMDB and falling back to IMDB/static IDs."""
    tmdb_results = fetch_tmdb_trending(user_agent)
    if tmdb_results:
        return tmdb_results

    headers = {"User-Agent": user_agent}
    response = requests.get(IMDB_TRENDING_URL, headers=headers, timeout=10)
    response.raise_for_status()
    ids = re.findall(r"/title/(tt\d+)/", response.text)
    results = _titles_from_ids(ids, user_agent)
    if results:
        return results
    return _titles_from_ids(DEFAULT_TRENDING_TITLE_IDS, user_agent)


def refresh_title_details(
    title_id: str, user_agent: str, normalized_type: str
) -> tuple[str | None, str | None, int | None, int | None, int | None, int | None, str | None]:
    """Refresh details for a title (ratings and metadata)."""
    try:
        imdb_rating, rotten_rating = _fetch_ratings(title_id, user_agent)
    except requests.RequestException:
        imdb_rating, rotten_rating = None, None
    try:
        (
            runtime_minutes,
            total_seasons,
            total_episodes,
            avg_episode_length,
            original_language,
        ) = _fetch_metadata(title_id, user_agent, normalized_type)
    except requests.RequestException:
        runtime_minutes = total_seasons = total_episodes = avg_episode_length = original_language = None
    with get_db_context() as conn:
        rating_cache_set(conn, title_id, imdb_rating, rotten_rating)
        metadata_cache_set(
            conn, title_id, runtime_minutes, total_seasons, total_episodes, avg_episode_length, original_language
        )
        conn.commit()
    return (
        imdb_rating,
        rotten_rating,
        runtime_minutes,
        total_seasons,
        total_episodes,
        avg_episode_length,
        original_language,
    )
