"""Pytest configuration and fixtures."""
from __future__ import annotations

import os
import tempfile

import pytest
from flask.testing import FlaskClient


class ShovoTestClient(FlaskClient):
    """Test client that supplies CSRF headers for mutating API requests."""

    def open(self, *args, **kwargs):
        method = kwargs.get("method")
        if method is None and len(args) >= 2:
            method = args[1]
        method = (method or "GET").upper()
        path = args[0] if args else kwargs.get("path", "")
        if method in {"POST", "PATCH", "DELETE"} and str(path).startswith("/api/"):
            with self.session_transaction() as session:
                token = session.setdefault("csrf_token", "test-csrf-token")
            headers = kwargs.setdefault("headers", {})
            headers.setdefault("X-CSRF-Token", token)
        return super().open(*args, **kwargs)

@pytest.fixture
def app():
    """Create application for testing with an isolated database per test."""
    test_db_fd, test_db_path = tempfile.mkstemp(prefix="shovo-test-", suffix=".sqlite3")
    os.close(test_db_fd)
    os.environ["SHOVO_TEST_DB"] = test_db_path

    # Import here to use test database
    from webapp import database

    # Override database path for tests
    original_db_path = database.DB_PATH
    database.DB_PATH = test_db_path

    from webapp import create_app

    app = create_app()
    app.test_client_class = ShovoTestClient
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # Initialize test database and reset process-local security buckets
    from webapp import routes
    routes._rate_limit_buckets.clear()

    with app.app_context():
        database.init_db()

    yield app

    # Cleanup
    database.DB_PATH = original_db_path
    os.environ.pop("SHOVO_TEST_DB", None)
    try:
        os.unlink(test_db_path)
    except FileNotFoundError:
        pass  # File may already be deleted


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI test runner."""
    return app.test_cli_runner()
