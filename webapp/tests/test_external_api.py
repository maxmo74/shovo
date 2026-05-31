"""Tests for external API functions."""
from __future__ import annotations

from webapp.external_api import fetch_trending, normalize_type_label, shrink_image_url
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
