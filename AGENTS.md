# AGENTS.md - Shovo Project Rules

Shovo is a public, reusable shared-watchlist web app. This repository must stay suitable for public GitHub use.

## Repository boundaries

- Public source repository: this Git checkout.
- Do commit: reusable application code, tests, generic documentation, example configs, and public-safe project skills.
- Do not commit: production secrets, real tokens, real environment files, production databases, private operational notes, host-specific credentials, or deployment-only local scripts that contain private infrastructure details.
- Host-specific documentation belongs outside the repository or in ignored local files only.

## Public vs local deployment content

Public repository content may include placeholders such as:

- `example.com`
- `/opt/shovo`
- `/etc/shovo.env`
- `shovo-uwsgi.service`

Public repository content must not include private-only values unless explicitly intended for publication, including:

- real API keys or GitHub tokens
- private hostnames, IP addresses, user names, or internal topology notes
- production database contents
- local-only operational credentials

## Development workflow

1. Inspect existing code and tests before changing behavior.
2. Prefer small, focused changes with matching tests.
3. Keep docs generic unless the file is explicitly an example or placeholder-based deployment guide.
4. Run tests before committing:
   ```bash
   cd webapp
   python -m pytest -q
   ```
   If only the deployed virtualenv has dependencies on the current host, use:
   ```bash
   /opt/shovo/webapp/.venv/bin/python -m pytest -q
   ```
5. Bump `APP_VERSION` in `webapp/routes.py` for user-visible or deployable changes.
6. Commit with a descriptive message and push only after tests pass and public/private separation has been checked.

## Deployment safety

- Never overwrite the production SQLite database during deploy.
- Back up the production database before risky changes or migrations.
- Validate service health after deployment.
- Deployment automation should live in generic public form in the repository and private host-specific form outside the repository when it contains local details.

## Security priorities

- Treat room URLs as bearer secrets unless/until server-side private-room authorization is complete.
- Add tests for security-sensitive changes.
- Avoid logging passwords, tokens, cookies, authorization headers, or full credential URLs.
- Keep dependency additions minimal and justified.

## UI changes

For CSS/UI changes, test at desktop and mobile widths. Use temporary screenshots/test artifacts under `/tmp`, not in the repository.
