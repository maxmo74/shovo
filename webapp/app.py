from __future__ import annotations

import os
from typing import Any

from flask import Flask, request

# Support both package and standalone imports
try:
    from .database import close_db, init_db
    from .routes import bp as main_bp
except ImportError:
    from database import close_db, init_db
    from routes import bp as main_bp


def create_app() -> Flask:
    """Create and configure the Flask application."""
    application = Flask(__name__)

    # Register teardown to close database connections
    application.teardown_appcontext(close_db)

    # Register blueprints
    application.register_blueprint(main_bp)

    # Add cache control headers
    @application.after_request
    def add_cache_headers(response: Any) -> Any:
        """Add cache control headers to responses."""
        if request.path.startswith("/static/") and request.path != "/static/sw.js":
            # Static files - cache for 1 year with version busting
            # Clear any default cache control first
            response.cache_control.clear()
            response.cache_control.max_age = 31536000  # 1 year
            response.cache_control.public = True
        elif request.path.startswith("/api/"):
            # API responses - no cache
            response.cache_control.clear()
            response.cache_control.no_cache = True
            response.cache_control.no_store = True
            response.cache_control.must_revalidate = True
        elif request.path.startswith("/r/") or request.path == "/":
            # HTML pages - no cache (always check server)
            response.cache_control.clear()
            response.cache_control.no_cache = True
            response.cache_control.must_revalidate = True
        return response

    # Initialize database on first request
    with application.app_context():
        init_db()

    return application


app = create_app()

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "").lower() in {"1", "true", "yes", "on"}
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
