"""Pytest configuration and fixtures."""
from __future__ import annotations

import os
import tempfile

import pytest

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
    app.config.update(
        {
            "TESTING": True,
        }
    )

    # Initialize test database
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
