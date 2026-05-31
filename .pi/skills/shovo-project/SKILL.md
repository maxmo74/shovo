---
name: shovo-project
description: Public-repository development workflow for the Shovo shared-watchlist app. Use when modifying Shovo code, docs, tests, security, or generic deployment examples while preserving public/private separation.
---

# Shovo Project Skill

## Core rule

Keep the GitHub repository public-safe. Do not commit secrets, private hostnames, production databases, credential URLs, or local-only deployment details.

## Repository content policy

Allowed in the public repo:

- Flask app code under `webapp/`
- tests under `webapp/tests/`
- generic documentation with placeholders
- example nginx/uWSGI/systemd configuration
- public-safe skills and agent instructions

Not allowed in the public repo:

- real API keys, GitHub tokens, passwords, or cookies
- production SQLite databases
- `.env` files
- local server notes containing private domains/IPs/topology
- deployment scripts with private-only assumptions unless parameterized/generic

## Development checklist

1. Read relevant code and tests first.
2. Make a focused change.
3. Add or update tests when behavior changes.
4. Bump `APP_VERSION` in `webapp/routes.py` for deployable changes.
5. Run tests:
   ```bash
   cd webapp
   python -m pytest -q
   ```
6. If dependencies are available only in the production venv on this host, use:
   ```bash
   cd webapp
   /opt/shovo/webapp/.venv/bin/python -m pytest -q
   ```
7. Before committing, run:
   ```bash
   git status --short
   git diff --check
   ```
8. Check that no private data is included:
   ```bash
   git diff --cached
   ```
9. Commit and push only after tests pass and the public/private boundary is clean.

## Security-sensitive work

For authentication, privacy, authorization, CSRF, rate limiting, or deployment hardening:

- document the threat model in `SECURITY.md` if it changes
- add regression tests for bypasses
- avoid logging credentials or room passwords
- prefer server-side enforcement over UI-only controls

## UI work

For CSS or template changes:

- test mobile and desktop layouts
- keep screenshots or temporary verification files under `/tmp`
- do not commit generated screenshots unless explicitly requested
