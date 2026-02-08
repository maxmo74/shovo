# Shovo - Project Philosophy

## An Experiment in AI-Developed Software

Shovo is a watchlist and movie/TV tracking web app where **100% of the code is written by AI agents**. The human role is limited to:

- Defining requirements and priorities
- Deploying to production
- Testing in real-world scenarios
- Providing feedback on user experience

This isn't AI-assisted development — it's AI-driven development with human oversight.

## What It Is

A functional, early-stage watchlist app. It works, it's simple, and it's honest about what it does. You can search for movies and shows, add them to a list, track what you've watched, and share lists with others via URL-based rooms.

## What It Isn't

- **Not production-hardened** — this is a personal project, not enterprise software
- **Not modular everywhere** — `main.js` is 1300+ lines; the CSS is 2600+ lines. Both could use splitting
- **Not fully tested** — no automated test suite beyond basic route tests

## Tech Stack

- **Backend**: Python / Flask
- **Frontend**: Vanilla JavaScript (ES modules), HTML, CSS
- **Database**: SQLite
- **APIs**: IMDb (search + ratings), OMDB (Rotten Tomatoes ratings)
- **No build step**: No bundlers, transpilers, or preprocessors

This stack is right for the scope. A framework would add complexity without adding value here.

## Genuine Strengths

- **No accounts needed** — room-based sharing via URLs is genuinely clever UX
- **Simple deployment** — single SQLite file, no external database
- **No build step** — edit and deploy, nothing to compile
- **AI-developed** — every line written by AI, which is the interesting part

## Known Limitations

- Room privacy uses password hashing but the room model is URL-based — anyone who knows the room name can see it exists
- Trending only works in production (IMDb blocks localhost)
- No automated test coverage for the frontend
- The codebase would benefit from splitting large files

## Development Model

1. **Human identifies need** — "Search results should show cached ratings"
2. **AI plans approach** — Analyzes codebase, proposes changes
3. **AI implements** — Writes code, CSS, tests
4. **AI verifies** — Visual testing, code analysis
5. **AI deploys** — Version bump, commit, push
6. **Human validates** — Tests in production, provides feedback
7. **Iterate** — Repeat as needed
