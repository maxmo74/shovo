"""Tests for external API functions."""
from __future__ import annotations

from webapp.external_api import fetch_tmdb_trending, fetch_trending, normalize_type_label, shrink_image_url, _fetch_ratings
from webapp.models import SearchResult


class TestNormalizeTypeLabel:
    """Tests for normalize_type_label function."""

    def test_normalize_movie(self):
        """Test normalizing movie type."""
        assert normalize_type_label("movie") == "movie"
        assert normalize_type_label("Movie") == "movie"
        assert normalize_type_label("MOVIE") == "movie"

    def test_normalize_tvseries(self):
        """Test normalizing TV series type."""
        assert normalize_type_label("tvSeries") == "tvseries"
        assert normalize_type_label("TV Series") == "tvseries"

    def test_normalize_feature(self):
        """Test normalizing feature type."""
        assert normalize_type_label("feature") == "feature"
        assert normalize_type_label("Feature") == "feature"

    def test_normalize_empty(self):
        """Test normalizing empty string."""
        assert normalize_type_label("") == ""

    def test_normalize_none(self):
        """Test normalizing None."""
        assert normalize_type_label(None) == ""

    def test_normalize_removes_non_alpha(self):
        """Test normalization removes non-alphabetic characters."""
        assert normalize_type_label("tv-series") == "tvseries"
        assert normalize_type_label("tv_movie") == "tvmovie"


class TestFetchRatings:
    """Tests for rating fetching."""

    def test_fetch_ratings_prefers_omdb(self, monkeypatch):
        """IMDB rating should come from OMDB to avoid brittle IMDB scraping."""

        def fail_imdb_fetch(*args, **kwargs):
            raise AssertionError("IMDB scraping should not be used when OMDB has ratings")

        monkeypatch.setattr(
            "webapp.external_api._fetch_omdb_title",
            lambda title_id, user_agent: {
                "Response": "True",
                "imdbRating": "8.2",
                "Ratings": [
                    {"Source": "Internet Movie Database", "Value": "8.2/10"},
                    {"Source": "Rotten Tomatoes", "Value": "93%"},
                ],
            },
        )
        monkeypatch.setattr("webapp.external_api.requests.get", fail_imdb_fetch)

        assert _fetch_ratings("tt0070735", "test-agent") == ("8.2", "93%")


class TestFetchTmdbTrending:
    """Tests for TMDB trending title fetching."""

    def test_fetch_tmdb_trending_maps_results_to_imdb_ids(self, monkeypatch):
        """TMDB trending results are converted to SearchResult items with IMDB IDs."""

        class Response:
            def __init__(self, payload):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        def fake_get(url, **kwargs):
            if "trending" in url:
                return Response(
                    {
                        "results": [
                            {
                                "adult": False,
                                "id": 100,
                                "media_type": "movie",
                                "title": "Trending Movie",
                                "release_date": "2026-05-31",
                                "original_language": "en",
                                "poster_path": "/poster.jpg",
                                "vote_average": 7.75,
                            },
                            {
                                "adult": False,
                                "id": 200,
                                "media_type": "tv",
                                "name": "Trending Show",
                                "first_air_date": "2026-05-30",
                                "original_language": "fr",
                                "poster_path": None,
                                "vote_average": 8,
                            },
                        ]
                    }
                )
            if "/movie/100/" in url:
                return Response({"imdb_id": "tt1000000"})
            if "/tv/200/" in url:
                return Response({"imdb_id": "tt2000000"})
            raise AssertionError(f"Unexpected URL: {url}")

        monkeypatch.setattr("webapp.external_api.TMDB_ACCESS_TOKEN", "token")
        monkeypatch.setattr("webapp.external_api.TMDB_API_KEY", None)
        monkeypatch.setattr("webapp.external_api.requests.get", fake_get)

        results = fetch_tmdb_trending("test-agent")

        assert [result.title_id for result in results] == ["tt1000000", "tt2000000"]
        assert [result.title for result in results] == ["Trending Movie", "Trending Show"]
        assert [result.type_label for result in results] == ["movie", "tvseries"]
        assert results[0].year == "2026"
        assert results[0].image == "https://image.tmdb.org/t/p/w185/poster.jpg"
        assert results[0].rating == "7.8"

    def test_fetch_tmdb_trending_returns_empty_without_credentials(self, monkeypatch):
        """TMDB is skipped when no credentials are configured."""
        monkeypatch.setattr("webapp.external_api.TMDB_ACCESS_TOKEN", None)
        monkeypatch.setattr("webapp.external_api.TMDB_API_KEY", None)

        assert fetch_tmdb_trending("test-agent") == []


class TestFetchTrending:
    """Tests for trending title fetching."""

    def test_fetch_trending_uses_fallback_when_chart_has_no_ids(self, monkeypatch):
        """IMDB WAF/empty chart responses should still produce fallback results."""

        class Response:
            text = ""

            def raise_for_status(self):
                return None

        def fake_get(*args, **kwargs):
            return Response()

        def fake_fetch_title_by_id(title_id, user_agent):
            return SearchResult(
                title_id=title_id,
                title=f"Title {title_id}",
                year="2024",
                original_language=None,
                type_label="movie",
                image=None,
                rating=None,
                rotten_tomatoes=None,
                runtime_minutes=None,
                total_seasons=None,
                total_episodes=None,
                avg_episode_length=None,
            )

        monkeypatch.setattr("webapp.external_api.fetch_tmdb_trending", lambda user_agent: [])
        monkeypatch.setattr("webapp.external_api.requests.get", fake_get)
        monkeypatch.setattr("webapp.external_api.fetch_title_by_id", fake_fetch_title_by_id)
        monkeypatch.setattr("webapp.external_api.DEFAULT_TRENDING_TITLE_IDS", ("tt0000001", "tt0000002"))

        results = fetch_trending("test-agent")

        assert [result.title_id for result in results] == ["tt0000001", "tt0000002"]

    def test_fetch_trending_prefers_chart_ids(self, monkeypatch):
        """Chart IDs are used when IMDB returns parseable chart HTML."""

        class Response:
            text = '<a href="/title/tt1234567/">One</a><a href="/title/tt7654321/">Two</a>'

            def raise_for_status(self):
                return None

        def fake_get(*args, **kwargs):
            return Response()

        def fake_fetch_title_by_id(title_id, user_agent):
            return SearchResult(
                title_id=title_id,
                title=f"Title {title_id}",
                year="2024",
                original_language=None,
                type_label="movie",
                image=None,
                rating=None,
                rotten_tomatoes=None,
                runtime_minutes=None,
                total_seasons=None,
                total_episodes=None,
                avg_episode_length=None,
            )

        monkeypatch.setattr("webapp.external_api.fetch_tmdb_trending", lambda user_agent: [])
        monkeypatch.setattr("webapp.external_api.requests.get", fake_get)
        monkeypatch.setattr("webapp.external_api.fetch_title_by_id", fake_fetch_title_by_id)
        monkeypatch.setattr("webapp.external_api.DEFAULT_TRENDING_TITLE_IDS", ("tt0000001",))

        results = fetch_trending("test-agent")

        assert [result.title_id for result in results] == ["tt1234567", "tt7654321"]


class TestShrinkImageUrl:
    """Tests for shrink_image_url function."""

    def test_shrink_standard_url(self):
        """Test shrinking a standard IMDB image URL."""
        url = "https://m.media-amazon.com/images/M/test._V1_SX300.jpg"
        result = shrink_image_url(url)
        assert "_V1_UX120_CR0,0,120,180_AL_" in result
        assert result.endswith(".jpg")

    def test_shrink_png_url(self):
        """Test shrinking a PNG URL."""
        url = "https://m.media-amazon.com/images/M/test._V1_SX300.png"
        result = shrink_image_url(url)
        assert "_V1_UX120_CR0,0,120,180_AL_" in result
        assert result.endswith(".png")

    def test_shrink_none(self):
        """Test shrinking None."""
        assert shrink_image_url(None) is None

    def test_shrink_empty(self):
        """Test shrinking empty string."""
        assert shrink_image_url("") is None

    def test_shrink_non_imdb_url(self):
        """Test shrinking non-IMDB URL returns unchanged."""
        url = "https://example.com/image.jpg"
        assert shrink_image_url(url) == url
