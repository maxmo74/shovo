# Shovo Operations Guide

This guide describes a generic self-hosted Shovo deployment. Keep real hostnames, tokens, private notes, and production data out of the public repository.

## Typical repository and deployment paths

Example paths used by the sample deployment:

- Source checkout: `/path/to/shovo`
- Production application: `/opt/shovo`
- SQLite database: `/opt/shovo/webapp/data.sqlite3`
- Environment file: `/etc/shovo.env`
- Systemd service: `shovo-uwsgi.service`
- Nginx site: `/etc/nginx/sites-enabled/example.com`

Adjust these for your host in private local documentation or automation.

## Runtime architecture

A common production setup is:

```text
Internet -> nginx :443 -> uWSGI 127.0.0.1:8001 -> Flask app -> SQLite
```

Static files can be served directly by Nginx from `/opt/shovo/webapp/static/`.

## Daily checks

```bash
systemctl status shovo-uwsgi.service --no-pager -l
systemctl status nginx --no-pager -l
curl -I https://example.com
journalctl -u shovo-uwsgi.service -n 100 --no-pager
```

## Test before deploying

```bash
cd /path/to/shovo/webapp
python -m pytest -q
```

If the production virtualenv is the only environment with dependencies installed:

```bash
cd /path/to/shovo/webapp
/opt/shovo/webapp/.venv/bin/python -m pytest -q
```

## Safe deployment checklist

1. Pull or checkout the intended commit.
2. Run the test suite.
3. Back up the production SQLite database.
4. Sync code to the production directory while excluding the production database and virtualenv.
5. Fix ownership and permissions.
6. Restart uWSGI.
7. Run an HTTP health check.
8. Inspect logs for startup errors.

Example sync command:

```bash
rsync -a --delete \
  --exclude webapp/data.sqlite3 \
  --exclude webapp/.venv \
  --exclude .git \
  /path/to/shovo/ /opt/shovo/
```

## Rollback outline

1. Identify the previous good Git commit:
   ```bash
   cd /path/to/shovo
   git log --oneline
   ```
2. Check it out or revert the bad commit.
3. Run tests.
4. Redeploy using the same safe deployment checklist.

If the database is suspected to be damaged, stop the service first and make a copy of `/opt/shovo/webapp/data.sqlite3` before attempting repair.

## Important files not in Git

- Environment files containing secrets such as `OMDB_API_KEY`.
- Production SQLite databases.
- Host-specific notes containing private domains, tokens, usernames, or infrastructure details.
