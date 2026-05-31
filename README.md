# Shovo - Shared Watchlist Web App

A lightweight web app that lets anyone with the URL create a shared movie/show list. It
uses IMDB search results (including thumbnails) and fetches IMDB ratings.

## Features

- Shared watchlists by room URL
- Watchlist and watched tabs
- IMDB search suggestions, thumbnails, ratings, and title metadata
- Trending-title discovery
- Drag/reorder and mobile swipe actions
- Optional room privacy UI with hashed stored passwords
- Progressive-web-app assets and service worker

## Local development

To run it:

```bash
cd webapp
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000` and share the room URL.

## Tests

```bash
cd webapp
python -m pytest -q
```

## Deployment and operations

Domain-scoped deployment configuration lives in `domain.example.ext/`. See
`domain.example.ext/README.md` for the uWSGI + Nginx setup on Debian/Ubuntu and the
associated TLS/security headers.

For a generic self-hosted workflow and safety checklist, see [`OPERATIONS.md`](OPERATIONS.md).

## Security

See [`SECURITY.md`](SECURITY.md) for the current security model, known gaps, and the hardening backlog.
