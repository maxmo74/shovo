# Shovo - Project Philosophy

## An Experiment in AI-Developed Software

Shovo is a watchlist and movie/TV tracking web app that serves as an experiment in **100% AI/LLM-developed software**. Every line of code, every CSS rule, every feature, and every bug fix is written by AI agents. The human role is limited to:

- Defining requirements and priorities
- Deploying to production
- Testing in real-world scenarios
- Providing feedback on user experience

This isn't AI-assisted development — it's AI-driven development with human oversight.

## Core Values

### Simple
No unnecessary complexity. Vanilla JavaScript instead of frameworks. SQLite instead of a database server. Flask instead of a heavyweight backend. Every dependency must justify its existence.

### Powerful
Despite its simplicity, Shovo delivers a full-featured experience: search, ratings from multiple sources, watchlist management, watched tracking, trending content, drag-to-reorder, and responsive mobile/desktop layouts.

### Free and Open Source
Shovo is free to use and open source. No accounts required, no tracking, no ads. Your data stays in your room — a simple URL-based namespace that requires no authentication.

### Community-Driven
Features are driven by real user needs discovered through actual usage, not hypothetical requirements.

## Tech Stack

- **Backend**: Python / Flask
- **Frontend**: Vanilla JavaScript (ES modules), HTML, CSS
- **Database**: SQLite
- **APIs**: IMDb (suggestions + ratings), Rotten Tomatoes (ratings)
- **No build step**: No bundlers, transpilers, or preprocessors

## LLM-Friendly Codebase

The codebase is intentionally structured for AI readability:

- Clear, descriptive naming conventions
- Modular file organization (separate JS modules for cards, modal, search, etc.)
- Comprehensive operating guidelines in `CLAUDE.md`
- Minimal abstraction layers — code does what it says
- Comments where logic isn't self-evident, not everywhere

## Development Model

1. **Human identifies need** — "The search results need to be more compact"
2. **AI plans approach** — Analyzes codebase, proposes changes
3. **AI implements** — Writes code, CSS, tests
4. **AI verifies** — Visual testing, code analysis, regression checks
5. **AI deploys** — Version bump, commit, push
6. **Human validates** — Tests in production, provides feedback
7. **Iterate** — Repeat as needed
