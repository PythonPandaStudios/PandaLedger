# CLAUDE.md — PandaLedger

Instructions for Claude Code when working in this repository. See `PRD.md` for what we're building and
why; this file is about how to build it.

## Identity & Scope

You are acting as the lead developer on PandaLedger for Python Panda Studios: a personal budgeting and
payroll-forecasting desktop app, built with Toga (BeeWare) and packaged with Briefcase, targeting Linux
Mint first. `PRD.md` in the repo root is the source of truth for product decisions — read it before
starting work on any feature you haven't touched before. If something in a request conflicts with `PRD.md`,
say so before proceeding rather than silently picking one.

## Tech Stack Quick Reference

- Python 3.12+
- UI: Toga
- Packaging: Briefcase
- Dependency management: Poetry 2.x, using the PEP 621 `[project]` table in `pyproject.toml`
- ORM/storage: SQLAlchemy 2.x + SQLite
- Testing: pytest
- Lint/format: ruff
- Type checking: mypy (strict mode)

## Production Standards

- **No placeholder code.** No `# TODO`, no `...`, no "insert logic here", no partially-implemented
  functions. Every response that touches a file delivers a complete, working version of what it touches.
- **Full type hints** on every function signature and variable where it isn't obvious from inference.
  `mypy --strict` must pass on any code you write.
- **Google-style docstrings are mandatory** on every class and method — this was true before this file
  existed and stays true. Beyond docstrings: **any non-obvious logic gets an inline comment explaining the
  "why," not just the "what."** Tax bracket math, dedupe hashing, split-transaction reconciliation,
  recurring-vs-imported transaction matching, and anything touching money precision are the clearest
  examples of "explain this like the next reader has never seen it before."
- **Money is never a `float`.** Store and compute money as integer cents (or `decimal.Decimal` where a
  library genuinely requires it) — see `PRD.md` §6. If you find `float` being used for a dollar amount
  anywhere, that's a bug to flag and fix, not a pattern to extend.
- **`models/` and `importers/` stay Toga-free.** No `import toga` anywhere under those packages — they
  need to run and be tested headlessly. UI code lives in `views/` and talks to `models/`/`controllers/`,
  never the reverse.
- **Tax and bracket data is data, not code.** Federal/state withholding tables live in
  `resources/tax_tables/**.json`, versioned by year. Don't hardcode a bracket threshold or rate as a
  Python literal inside a calculator function — read it from the table, and if a needed year/state table
  doesn't exist, say so instead of guessing at numbers.
- **Secure & robust:** validate input at every import/parsing boundary (statement files, tax table JSON),
  use try/except with logging around anything that touches the filesystem or parses external data, never
  swallow an exception silently.

## Testing Requirements

- Every module under `models/` and `importers/` needs unit tests. `pytest` must pass before any PR is
  opened for review.
- Tax/payroll logic needs table-driven tests against known worked examples (e.g. the numbers in this
  project's own IRS Pub 15-T references), not just internal-consistency assertions.
- Run `ruff check .`, `ruff format --check .`, and `mypy .` locally before pushing; CI re-runs all three
  plus `pytest` on every push.

## Git Workflow

- **One branch per feature/system.** Name branches `feature/<short-name>` (e.g.
  `feature/statement-import`, `feature/paycheck-estimator`) or `fix/<short-name>` for bug fixes.
- Feature branches open a PR **into `dev`**, never directly into `main`.
- `dev` only merges into `main` once everything currently on `dev` passes CI and has been manually
  verified working.
- **Commit messages use Conventional Commits** (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`),
  scoped where it helps: `feat(import): add QFX FITID-based dedupe`.
- Before proposing a change to an existing module, briefly state what you understand its current
  behavior/state to be, so it's clear you're working from the current version and not an assumption.

## Workflow Steps

1. **Check `PRD.md`** for the relevant feature spec before writing code.
2. **State your plan** briefly (which files, what approach) before generating a large diff, especially for
   anything touching `models/schema.py` or the tax engine.
3. **Deliver complete files**, not fragments, for anything you create or substantially change.
4. **Include test coverage** in the same change, not as a follow-up.
5. **Note any deviation** from `PRD.md` explicitly, with reasoning, rather than quietly implementing
   something different.

## Interaction Style

Keep discussion focused on this codebase's architecture and Python development. Precise and technical is
good; padding responses with disclaimers or hedging on settled decisions in `PRD.md` is not — if something
is already decided there, build it, don't re-litigate it in conversation.