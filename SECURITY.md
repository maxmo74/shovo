# Security Notes

## Current model

Shovo is a shared-list web app. Room IDs are URLs, so anyone with a room URL can access the room unless stronger access control is added.

A recommended production setup places Flask/uWSGI on localhost behind Nginx with HTTPS, HSTS, frame protection, basic content security policy, and static file serving.

## Secrets and data

- Environment files store deployment secrets and should be readable only by root and the service user.
- The production SQLite database stores app data and should be readable/writable only by the service user and administrators.
- Never commit production databases, `.env` files, API keys, GitHub tokens, or credential URLs.

## Known security gaps to improve

1. **Room privacy is not full server-side authorization yet.** Passwords are hashed, but list read/write API endpoints currently trust possession of the room ID. The UI asks for a password for private rooms, but API enforcement should be added server-side before privacy is treated as strong access control.
2. **No CSRF protection.** Mutating endpoints accept JSON POST/PATCH/DELETE requests without CSRF tokens. Same-origin browser requests are the intended use, but formal CSRF protection should be added.
3. **No API rate limiting.** Search, password verification, and mutating endpoints should have rate limits to reduce brute-force and abuse risk.
4. **Inline JavaScript is allowed by CSP.** Some deployments may need `'unsafe-inline'` for scripts. This should be removed after inline handlers/scripts are eliminated or nonce support is added.
5. **Room IDs are bearer secrets.** Public rooms rely on unguessable/random room IDs or user-chosen names. User-chosen room names may be guessable.

## Recommended hardening backlog

- Add server-side authorization for private-room list APIs using signed Flask sessions or short-lived room access tokens.
- Add rate limiting for `/api/room/verify-password`, `/api/search`, `/api/trending`, and mutating list endpoints.
- Add CSRF protection for all mutating endpoints.
- Tighten file permissions for the production SQLite database.
- Add safer deployment automation with pre-deploy tests, database backup, config tests, and post-deploy health checks.
- Reduce CSP script permissions where possible.

## Reporting issues

Open a private issue or contact the maintainer directly if a vulnerability exposes private room data, production secrets, or write access.
