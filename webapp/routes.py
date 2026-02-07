from __future__ import annotations

import threading
import time
from typing import Any

import requests
from flask import Blueprint, jsonify, redirect, render_template, request

# Support both package and standalone imports
try:
    from .database import get_db, get_db_context, migrate_db
    from .external_api import (
        ALLOWED_TYPE_LABELS,
        MAX_RESULTS,
        fetch_suggestions,
        fetch_trending,
        get_metadata,
        get_ratings,
        normalize_type_label,
        refresh_title_details,
    )
    from .utils import (
        default_room,
        parse_watched,
        request_user_agent,
        room_from_request,
        sanitize_room,
        serialize_result,
    )
except ImportError:
    from database import get_db, get_db_context, migrate_db
    from external_api import (
        ALLOWED_TYPE_LABELS,
        MAX_RESULTS,
        fetch_suggestions,
        fetch_trending,
        get_metadata,
        get_ratings,
        normalize_type_label,
        refresh_title_details,
    )
    from utils import (
        default_room,
        parse_watched,
        request_user_agent,
        room_from_request,
        sanitize_room,
        serialize_result,
    )

APP_VERSION = "1.6.57"
DEFAULT_ROOM_COOKIE = "shovo_default_room"
TRENDING_TTL_SECONDS = 60 * 60

bp = Blueprint("main", __name__)

_refresh_lock = threading.Lock()
_refresh_state: dict[str, dict[str, int | bool]] = {}
_trending_lock = threading.Lock()
_trending_cache: dict[str, Any] = {"data": [], "fetched_at": 0, "refreshing": False}


@bp.route("/")
def root() -> Any:
    """Redirect to the default room or new room."""
    default_room_value = request.cookies.get(DEFAULT_ROOM_COOKIE)
    if default_room_value:
        return redirect(f"/r/{default_room_value}")
    return redirect("/r/new")


@bp.route("/r/<room>")
def room(room: str) -> Any:
    """Render the main application page for a room."""
    if room == "new":
        default_room_value = request.cookies.get(DEFAULT_ROOM_COOKIE)
        if default_room_value:
            return redirect(f"/r/{default_room_value}")
        return redirect(f"/r/{default_room()}")
    _ensure_trending_preload(request_user_agent())
    return render_template("index.html", room=room, app_version=APP_VERSION)


@bp.route("/static/sw.js")
def service_worker() -> Any:
    """Serve the service worker with the current app version."""
    from flask import make_response

    response = make_response(render_template("sw.js.j2", app_version=APP_VERSION))
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Service-Worker-Allowed"] = "/"
    return response


@bp.route("/api/version")
def api_version() -> Any:
    """Get the current app version."""
    return jsonify({"version": APP_VERSION})


@bp.route("/api/search")
def api_search() -> Any:
    """Search for titles."""
    query = request.args.get("q", "")
    user_agent = request_user_agent()
    try:
        results = fetch_suggestions(query, user_agent)
        return jsonify({"results": [serialize_result(result) for result in results[:MAX_RESULTS]]})
    except requests.RequestException as exc:
        return jsonify({"error": "imdb_fetch_failed", "detail": str(exc), "results": []})


@bp.route("/api/details")
def api_details() -> Any:
    """Get details for a single title."""
    title_id = request.args.get("title_id")
    if not title_id:
        return jsonify({"error": "missing_title_id"}), 400
    type_label = request.args.get("type_label")
    normalized_type = normalize_type_label(type_label)
    if normalized_type not in ALLOWED_TYPE_LABELS:
        normalized_type = "movie"
    user_agent = request_user_agent()
    runtime_minutes, total_seasons, total_episodes, avg_episode_length, original_language = get_metadata(
        title_id, user_agent, normalized_type
    )
    rating, rotten_tomatoes = get_ratings(title_id, user_agent)
    return jsonify(
        {
            "rating": rating,
            "rotten_tomatoes": rotten_tomatoes,
            "runtime_minutes": runtime_minutes,
            "total_seasons": total_seasons,
            "total_episodes": total_episodes,
            "avg_episode_length": avg_episode_length,
            "original_language": original_language,
        }
    )


@bp.route("/api/refresh", methods=["POST"])
def api_refresh() -> Any:
    """Start a background refresh of ratings and metadata."""
    if not request.is_json:
        return jsonify({"error": "invalid_payload"}), 400
    room = room_from_request()
    if not room:
        return jsonify({"error": "missing_room"}), 400
    user_agent = request_user_agent()
    with _refresh_lock:
        state = _refresh_state.get(room)
        if state and state.get("refreshing"):
            return jsonify({"error": "refresh_in_progress"}), 409
    total = _start_refresh(room, user_agent)
    return jsonify({"status": "started", "total": total})


@bp.route("/api/refresh/status")
def api_refresh_status() -> Any:
    """Get the status of a background refresh."""
    room = request.args.get("room", "")
    if not room:
        return jsonify({"error": "missing_room"}), 400
    with _refresh_lock:
        state = _refresh_state.get(room, {"refreshing": False, "processed": 0, "total": 0})
        return jsonify(state)


@bp.route("/api/trending")
def api_trending() -> Any:
    """Get trending titles."""
    user_agent = request_user_agent()
    try:
        results = _get_trending_cached(user_agent)
    except requests.RequestException as exc:
        return jsonify({"error": "imdb_fetch_failed", "detail": str(exc)}), 502
    return jsonify({"results": [serialize_result(result) for result in results]})


@bp.route("/api/list", methods=["GET"])
def api_list() -> Any:
    """Get the list of titles for a room."""
    room = room_from_request() or request.args.get("room", "")
    if not room:
        return jsonify({"error": "missing_room"}), 400
    status = request.args.get("status", "unwatched")
    watched_flag = 1 if status == "watched" else 0
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = max(int(request.args.get("per_page", MAX_RESULTS)), 1)
    except (ValueError, TypeError):
        return jsonify({"error": "invalid_pagination_params"}), 400
    offset = (page - 1) * per_page
    conn = get_db()
    migrate_db(conn)
    total_count = conn.execute(
        "SELECT COUNT(*) FROM lists WHERE room = ? AND watched = ?",
        (room, watched_flag),
    ).fetchone()[0]
    watched_count = conn.execute(
        "SELECT COUNT(*) FROM lists WHERE room = ? AND watched = 1",
        (room,),
    ).fetchone()[0]
    unwatched_count = conn.execute(
        "SELECT COUNT(*) FROM lists WHERE room = ? AND watched = 0",
        (room,),
    ).fetchone()[0]
    rows = conn.execute(
        """
        SELECT * FROM lists
        WHERE room = ? AND watched = ?
        ORDER BY (position IS NULL) ASC, position DESC, added_at DESC
        LIMIT ? OFFSET ?
        """,
        (room, watched_flag, per_page, offset),
    ).fetchall()
    total_pages = max((total_count + per_page - 1) // per_page, 1)
    return jsonify(
        {
            "items": [dict(row) for row in rows],
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "total_count": total_count,
            "counts": {"watched": watched_count, "unwatched": unwatched_count},
        }
    )


def _set_trending_cache(results: list[Any]) -> None:
    now = int(time.time())
    _trending_cache["data"] = results
    _trending_cache["fetched_at"] = now


def _refresh_trending_async(user_agent: str) -> None:
    def _run() -> None:
        try:
            results = fetch_trending(user_agent)
        except requests.RequestException:
            with _trending_lock:
                _trending_cache["refreshing"] = False
            return
        with _trending_lock:
            _set_trending_cache(results)
            _trending_cache["refreshing"] = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()


def _ensure_trending_preload(user_agent: str) -> None:
    now = int(time.time())
    with _trending_lock:
        data = _trending_cache.get("data", [])
        fetched_at = int(_trending_cache.get("fetched_at", 0))
        refreshing = bool(_trending_cache.get("refreshing"))
        is_fresh = data and fetched_at + TRENDING_TTL_SECONDS > now
        if refreshing or is_fresh:
            return
        _trending_cache["refreshing"] = True
    _refresh_trending_async(user_agent)


def _get_trending_cached(user_agent: str) -> list[Any]:
    now = int(time.time())
    with _trending_lock:
        data = _trending_cache.get("data", [])
        fetched_at = int(_trending_cache.get("fetched_at", 0))
        refreshing = bool(_trending_cache.get("refreshing"))
        is_fresh = data and fetched_at + TRENDING_TTL_SECONDS > now
        if is_fresh:
            return data
        if data and not refreshing:
            _trending_cache["refreshing"] = True
            _refresh_trending_async(user_agent)
            return data
        if refreshing and not data:
            pass
        else:
            _trending_cache["refreshing"] = True
    if refreshing and not data:
        deadline = time.time() + 2
        while time.time() < deadline:
            with _trending_lock:
                data = _trending_cache.get("data", [])
                fetched_at = int(_trending_cache.get("fetched_at", 0))
                if data and fetched_at + TRENDING_TTL_SECONDS > int(time.time()):
                    return data
            time.sleep(0.1)
    try:
        results = fetch_trending(user_agent)
        with _trending_lock:
            _set_trending_cache(results)
        return results
    finally:
        with _trending_lock:
            _trending_cache["refreshing"] = False


@bp.route("/api/list", methods=["POST"])
def api_add() -> Any:
    """Add a title to a list."""
    if not request.is_json:
        return jsonify({"error": "invalid_payload"}), 400
    room = room_from_request()
    if not room:
        return jsonify({"error": "missing_room"}), 400
    data = request.json
    title_id = data.get("title_id")
    title = data.get("title")
    if not title_id or not title:
        return jsonify({"error": "missing_title"}), 400
    watched = parse_watched(data.get("watched", 0))
    conn = get_db()
    migrate_db(conn)
    next_position = conn.execute(
        "SELECT COALESCE(MAX(position), 0) + 1 FROM lists WHERE room = ? AND watched = ?",
        (room, watched),
    ).fetchone()[0]
    conn.execute(
        """
        REPLACE INTO lists (
            room, title_id, title, year, original_language, type_label, image, rating, rotten_tomatoes,
            runtime_minutes, total_seasons, total_episodes, avg_episode_length, added_at, watched
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            room,
            title_id,
            title,
            data.get("year"),
            data.get("original_language"),
            data.get("type_label"),
            data.get("image"),
            data.get("rating"),
            data.get("rotten_tomatoes"),
            data.get("runtime_minutes"),
            data.get("total_seasons"),
            data.get("total_episodes"),
            data.get("avg_episode_length"),
            int(time.time()),
            watched,
        ),
    )
    conn.execute(
        "UPDATE lists SET position = ? WHERE room = ? AND title_id = ?",
        (next_position, room, title_id),
    )
    conn.commit()
    return jsonify({"status": "ok"})


@bp.route("/api/list", methods=["PATCH"], endpoint="api_list_patch")
def api_patch_list() -> Any:
    """Update the watched status of a title."""
    if not request.is_json:
        return jsonify({"error": "invalid_payload"}), 400
    room = room_from_request()
    if not room:
        return jsonify({"error": "missing_room"}), 400
    title_id = request.json.get("title_id")
    watched = parse_watched(request.json.get("watched"))
    if not title_id:
        return jsonify({"error": "missing_title_id"}), 400
    conn = get_db()
    migrate_db(conn)
    conn.execute(
        "UPDATE lists SET watched = ? WHERE room = ? AND title_id = ?",
        (watched, room, title_id),
    )
    conn.commit()
    return jsonify({"status": "ok"})


@bp.route("/api/list/order", methods=["PATCH"])
def api_order() -> Any:
    """Update the order of titles in a list."""
    if not request.is_json:
        return jsonify({"error": "invalid_payload"}), 400
    room = room_from_request()
    if not room:
        return jsonify({"error": "missing_room"}), 400
    order = request.json.get("order")
    if not isinstance(order, list) or not order:
        return jsonify({"error": "invalid_order"}), 400
    conn = get_db()
    migrate_db(conn)
    total = len(order)
    for index, title_id in enumerate(order):
        position = total - index
        conn.execute(
            "UPDATE lists SET position = ? WHERE room = ? AND title_id = ?",
            (position, room, title_id),
        )
    conn.commit()
    return jsonify({"status": "ok"})


@bp.route("/api/list", methods=["DELETE"])
def api_delete() -> Any:
    """Delete a title from a list."""
    if not request.is_json:
        return jsonify({"error": "invalid_payload"}), 400
    room = room_from_request()
    if not room:
        return jsonify({"error": "missing_room"}), 400
    title_id = request.json.get("title_id")
    if not title_id:
        return jsonify({"error": "missing_title_id"}), 400
    conn = get_db()
    migrate_db(conn)
    conn.execute(
        "DELETE FROM lists WHERE room = ? AND title_id = ?",
        (room, title_id),
    )
    conn.commit()
    return jsonify({"status": "ok"})


@bp.route("/api/list/rename", methods=["PATCH"])
def api_rename_list() -> Any:
    """Rename a list (change room ID)."""
    if not request.is_json:
        return jsonify({"error": "invalid_payload"}), 400
    room = room_from_request()
    if not room:
        return jsonify({"error": "missing_room"}), 400
    next_room = sanitize_room(request.json.get("next_room"))
    if not next_room:
        return jsonify({"error": "missing_next_room"}), 400
    if next_room == room:
        return jsonify({"status": "ok", "room": room})
    conn = get_db()
    migrate_db(conn)
    existing = conn.execute(
        "SELECT 1 FROM lists WHERE room = ? LIMIT 1",
        (next_room,),
    ).fetchone()
    if existing:
        return (
            jsonify(
                {
                    "error": "room_exists",
                    "message": "That List ID already exists. Pick another name.",
                }
            ),
            409,
        )
    conn.execute("UPDATE lists SET room = ? WHERE room = ?", (next_room, room))
    conn.commit()
    return jsonify({"status": "ok", "room": next_room})


def _start_refresh(room: str, user_agent: str) -> int:
    """Start a background refresh of all titles in a room."""
    with get_db_context() as conn:
        migrate_db(conn)
        rows = conn.execute(
            "SELECT title_id, type_label FROM lists WHERE room = ?",
            (room,),
        ).fetchall()
    items = [(row["title_id"], row["type_label"]) for row in rows]
    total = len(items)
    with _refresh_lock:
        _refresh_state[room] = {"refreshing": True, "processed": 0, "total": total}

    def _run_refresh() -> None:
        with get_db_context() as conn:
            migrate_db(conn)
            for title_id, type_label in items:
                normalized_type = normalize_type_label(type_label)
                if normalized_type not in ALLOWED_TYPE_LABELS:
                    normalized_type = "movie"
                (
                    imdb_rating,
                    rotten_rating,
                    runtime_minutes,
                    total_seasons,
                    total_episodes,
                    avg_episode_length,
                    original_language,
                ) = refresh_title_details(title_id, user_agent, normalized_type)
                conn.execute(
                    """
                    UPDATE lists
                    SET rating = ?, rotten_tomatoes = ?, runtime_minutes = ?, total_seasons = ?,
                        total_episodes = ?, avg_episode_length = ?, original_language = ?
                    WHERE room = ? AND title_id = ?
                    """,
                    (
                        imdb_rating,
                        rotten_rating,
                        runtime_minutes,
                        total_seasons,
                        total_episodes,
                        avg_episode_length,
                        original_language,
                        room,
                        title_id,
                    ),
                )
                conn.commit()
                with _refresh_lock:
                    state = _refresh_state.get(room)
                    if state:
                        state["processed"] = int(state.get("processed", 0)) + 1
            with _refresh_lock:
                state = _refresh_state.get(room)
                if state:
                    state["refreshing"] = False

    thread = threading.Thread(target=_run_refresh, daemon=True)
    thread.start()
    return total
